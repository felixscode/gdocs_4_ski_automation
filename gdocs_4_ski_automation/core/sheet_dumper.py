from datetime import datetime
from time import sleep
from typing import Dict, List

import gspread
import numpy as np
from gspread.exceptions import APIError

from gdocs_4_ski_automation.core.ctypes import Course, Registration
from gdocs_4_ski_automation.utils.utils import GoogleAuthenticatorInterface


class GDocsDumper:
    def __init__(
        self,
        registrations: List[Registration],
        sheet_ids: Dict[str, str],
        g_clients: gspread.Client,
    ):
        """
        Initialize the GDocsDumper.

        Args:
            registrations: List of registration objects.
            sheet_ids: Dictionary containing sheet IDs.
            g_clients: Google client object.
        """
        self.registrations = registrations
        self.sheet_ids = sheet_ids
        self.gc = g_clients
        self._sheets_cache: Dict[str, gspread.Spreadsheet] = {}

    def _get_sheet(self, sheet_key: str) -> gspread.Spreadsheet:
        """
        Get a cached sheet object to minimize API calls.

        Args:
            sheet_key: Key from sheet_ids dict ('registrations', 'db', etc.).

        Returns:
            Cached spreadsheet object.
        """
        if sheet_key not in self._sheets_cache:
            self._sheets_cache[sheet_key] = self.gc.open_by_key(self.sheet_ids[sheet_key])
        return self._sheets_cache[sheet_key]

    def _batch_update_with_retry(
        self,
        worksheet: gspread.Worksheet,
        updates: List[Dict],
        max_retries: int = 3,
    ) -> None:
        """
        Execute batch update with exponential backoff retry on rate limits.

        Args:
            worksheet: Target worksheet.
            updates: List of update dictionaries with 'range' and 'values'.
            max_retries: Maximum number of retry attempts.
        """
        for attempt in range(max_retries):
            try:
                worksheet.batch_update(updates)
                return
            except APIError as e:
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                    sleep(wait_time)
                    continue
                raise

    def _dump_overview(self) -> None:
        """
        Dump overview data to the 'Übersicht' worksheet using batch update.
        Reduces from 12 individual API calls to 1 batch call.
        """
        sheet = self._get_sheet("registrations")
        worksheet = sheet.worksheet("Übersicht")

        all_participants = [p for r in self.registrations for p in r.participants]
        total_participants = len(all_participants)
        total_zw = len(
            [
                p
                for p in all_participants
                if p.course in [Course.ZWEGERL, Course.ZWEGERL_SNOWBOARD]
            ]
        )
        total_normal = len(
            [p for p in all_participants if p.course in [Course.SKI, Course.SNOWBOARD]]
        )
        num_registrations = len(self.registrations)
        paid = len([r for r in self.registrations if r.payment.payed])
        not_paid = len([r for r in self.registrations if not r.payment.payed])
        paid_ratio = paid / len(self.registrations) if self.registrations else 0
        registrations_per_contact = (
            np.mean([len(r.participants) for r in self.registrations])
            if self.registrations
            else 0
        )
        mean_age = np.mean([p.age for p in all_participants]) if all_participants else 0
        min_age = min([p.age for p in all_participants]) if all_participants else 0
        max_age = max([p.age for p in all_participants]) if all_participants else 0
        last_gcloud_call = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

        # Use batch update instead of individual update_acell calls
        cell_updates = [
            {"range": "B4", "values": [[total_zw]]},
            {"range": "B5", "values": [[total_normal]]},
            {"range": "B6", "values": [[total_participants]]},
            {"range": "B7", "values": [[num_registrations]]},
            {"range": "B10", "values": [[paid]]},
            {"range": "B11", "values": [[not_paid]]},
            {"range": "B12", "values": [[paid_ratio]]},
            {"range": "B15", "values": [[registrations_per_contact]]},
            {"range": "B16", "values": [[mean_age]]},
            {"range": "B17", "values": [[min_age]]},
            {"range": "B18", "values": [[max_age]]},
            {"range": "B19", "values": [[last_gcloud_call]]},
        ]
        self._batch_update_with_retry(worksheet, cell_updates)

    def _dump_paid(self) -> None:
        """
        Dump paid registration data to the 'Bezahlung' worksheet.
        Combines two updates into a single batch operation.
        """
        paid_counter = 0
        data = []

        for registration in self.registrations:
            data.append(
                [
                    int(registration._id),
                    registration.contact.name.first,
                    registration.contact.name.last,
                    registration.contact.mail,
                    registration.contact.tel,
                    registration.payment.amount,
                    bool(registration.payment.payed),
                ]
            )
            if registration.payment.payed:
                paid_counter += 1

        data = sorted(data, key=lambda x: x[0])
        sheet = self._get_sheet("registrations")
        worksheet = sheet.worksheet("Bezahlung")

        # Batch update both data and summary
        updates = [
            {"range": "A3", "values": data},
            {"range": "G1", "values": [[f"Insgesamt Bezahlt: {paid_counter}/{len(data)}"]]},
        ]
        self._batch_update_with_retry(worksheet, updates)

    def _dump_member(self) -> None:
        """
        Dump member data to the 'Mitglied' worksheet.
        Uses single update call for all data.
        """
        data = []
        p_names = []

        for registration in self.registrations:
            for participant in registration.participants:
                if participant.name not in p_names:
                    data.append(
                        [
                            int(registration._id),
                            participant.name.first,
                            participant.name.last,
                            registration.contact.name.first,
                            registration.contact.name.last,
                            registration.contact.mail,
                            registration.contact.tel,
                        ]
                    )
                    p_names.append(participant.name)

        data = sorted(data, key=lambda x: (x[0], x[1]))
        sheet = self._get_sheet("registrations")
        worksheet = sheet.worksheet("Mitglied")
        worksheet.update("A3", data)

    def _dump_zwergerl(self) -> None:
        """
        Dump Zwergerl course data to the 'Zwergerl' worksheet.
        Combines clear, data update, and count into batch operation.
        """
        data = []

        for registration in self.registrations:
            for p in registration.participants:
                if p.course in [Course.ZWEGERL, Course.ZWEGERL_SNOWBOARD]:
                    data.append(
                        [
                            "ski" if p.course == Course.ZWEGERL else "snowboard",
                            p.name.first,
                            p.name.last,
                            p.age,
                            registration.contact.mail,
                            registration.contact.tel,
                            registration.contact.name.first,
                            registration.contact.name.last,
                            p.notes,
                        ]
                    )

        sheet = self._get_sheet("registrations")
        worksheet = sheet.worksheet("Zwergerl")

        # Clear and update in batch
        worksheet.batch_clear(["A3:I1000"])
        updates = [
            {"range": "A3", "values": data},
            {"range": "G1", "values": [[len(data)]]},
        ]
        self._batch_update_with_retry(worksheet, updates)

    def _dump_normal(self) -> None:
        """
        Dump normal course data to the 'Kurse' worksheet.
        Combines clear, data update, and count into batch operation.
        """
        data = []

        for registration in self.registrations:
            for p in registration.participants:
                if p.course in [Course.SKI, Course.SNOWBOARD]:
                    data.append(
                        [
                            "ski" if p.course == Course.SKI else "snowboard",
                            p.name.first,
                            p.name.last,
                            p.age,
                            registration.contact.mail,
                            registration.contact.tel,
                            registration.contact.name.first,
                            registration.contact.name.last,
                            p.pre_course,
                            p.notes,
                        ]
                    )

        sheet = self._get_sheet("registrations")
        worksheet = sheet.worksheet("Kurse")

        # Clear and update in batch
        worksheet.batch_clear(["A3:J1000"])
        updates = [
            {"range": "A3", "values": data},
            {"range": "G1", "values": [[len(data)]]},
        ]
        self._batch_update_with_retry(worksheet, updates)

    def dump_mail_flags(self) -> None:
        """
        Dump mail flags to the 'Formularantworten' worksheet in the 'db' sheet.
        Reduces from 3N+2 individual API calls to 2 batch calls.
        """
        sheet = self._get_sheet("db")
        worksheet = sheet.worksheet("Formularantworten")

        # First update: registration IDs
        registration_id = [[str(r._id)] for r in self.registrations]
        worksheet.update("BH2", registration_id)

        # Get all values once
        cell_values = worksheet.get_all_values()
        ids = list(zip(*cell_values))[-1][1:]
        id_mapping = {
            _id: {
                "r_cell": f"BF{int(_id) + 1}",
                "p_cell": f"BG{int(_id) + 1}",
                "price_cell": f"BE{int(_id) + 1}",
            }
            for _id in ids
        }

        # Prepare batch updates for all flags
        updates = []
        for registration in self.registrations:
            p_mail_sent = "TRUE" if registration.payment_mail_sent else "FALSE"
            r_mail_sent = "TRUE" if registration.registration_mail_sent else "FALSE"

            updates.extend(
                [
                    {
                        "range": id_mapping[str(registration._id)]["r_cell"],
                        "values": [[r_mail_sent]],
                    },
                    {
                        "range": id_mapping[str(registration._id)]["p_cell"],
                        "values": [[p_mail_sent]],
                    },
                    {
                        "range": id_mapping[str(registration._id)]["price_cell"],
                        "values": [[registration.payment.amount]],
                    },
                ]
            )

        # Single batch update for all mail flags
        self._batch_update_with_retry(worksheet, updates)

    def dump_registrations(self) -> None:
        """
        Dump all registration data to the respective worksheets.
        Adds small delays between operations to respect API rate limits.
        """
        self._dump_overview()
        sleep(0.3)  # Brief pause to respect rate limits
        self._dump_paid()
        sleep(0.3)
        self._dump_member()
        sleep(0.3)
        self._dump_zwergerl()
        sleep(0.3)
        self._dump_normal()
        sleep(0.3)
        self.dump_mail_flags()


if __name__ == "__main__":
    from gdocs_4_ski_automation.core.factories import GDocsRegistrationFactory

    sheet_ids = {
        "settings": "1SteMGOoigoPyZMJsB5GG82K4WNh-N2AQIck_xtrmtz8",
        "registrations": "11FLy4qTOScUOLj4xGVPMy12940DsOYz2pmoPDf9pDhA",
        "db": "1VUuX4UbsWsxd5QUKA7FjsebU2uPTs80dBSSn4Tay_Vk",
    }

    google_authenticator = GoogleAuthenticatorInterface("data/dependencies/client_secret.json")
    google_client = google_authenticator.gspread
    factory = GDocsRegistrationFactory(sheet_ids, google_client)
    registrations = factory.build_registrations()
    dumper = GDocsDumper(registrations, sheet_ids, google_client)
    dumper.dump_registrations()