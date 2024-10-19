from gdocs_4_ski_automation.utils.utils import GoogleAuthenticatorInterface
from gdocs_4_ski_automation.core.ctypes import Course
import numpy as np
from datetime import datetime

class GDocsDumper():
    def __init__(self,registrations, sheet_ids,g_clients):
        self.registrations = registrations
        self.sheet_ids = sheet_ids
        self.gc = g_clients


    def _dump_overview(self):
        sheet = self.gc.open_by_key(self.sheet_ids['registrations'])
        worksheet = sheet.worksheet("Übersicht")
        all_participants = [p for r in self.registrations for p in r.participants]
        total_participants = len(all_participants)
        total_zw = len([p for p in all_participants if p.course in [Course.ZWEGERL,Course.ZWEGERL_SNOWBOARD]])
        total_normal = len([p for p in all_participants if p.course in [Course.SKI,Course.SNOWBOARD]])
        num_registrations = len(self.registrations)
        paid = len([r for r in self.registrations if r.payment.payed])
        not_paid = len([r for r in self.registrations if not r.payment.payed])
        paid_ratio = paid/len(self.registrations)
        registrations_per_contatact = np.mean([len(r.participants) for r in self.registrations])
        mean_age = np.mean([p.age for p in all_participants])
        min_age = min([p.age for p in all_participants])
        max_age = max([p.age for p in all_participants])
        last_gcloud_call = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        cell_mapping = {
            "B4": total_zw,
            "B5": total_normal,
            "B6": total_participants,
            "B7": num_registrations,
            "B10": paid,
            "B11": not_paid,
            "B12": paid_ratio,
            "B15": registrations_per_contatact,
            "B16": mean_age,
            "B17": min_age,
            "B18": max_age,
            "B19": last_gcloud_call

        }

        for cell, value in cell_mapping.items():
            worksheet.update_acell(cell, value)


    def _dump_paid(self):
        paid_counter = 0
        data = []
        for registration in self.registrations:
            data.append([
                    int(registration._id),
                    registration.contact.name.first,
                    registration.contact.name.last,
                    registration.contact.mail,
                    registration.contact.tel,
                    registration.payment.amount,
                    bool(registration.payment.payed)
                ])
            if registration.payment.payed:
                paid_counter += 1

        data = sorted(data,key=lambda x: x[0])
        sheet = self.gc.open_by_key(self.sheet_ids['registrations'])
        worksheet = sheet.worksheet("Bezahlung")
        worksheet.batch_clear(["A3:F1000"])
        worksheet.update("A3",values = data)

        worksheet.update_acell("G1",f"Insgesammt Bezahlt: {paid_counter}/{len(data)}")

    def _dump_member(self):

        data = []
        p_names = []
        for registration in self.registrations:
            for participant in registration.participants:
                if participant.name not in p_names:
                    data.append([
                        int(registration._id),
                        participant.name.first,
                        participant.name.last,
                        registration.contact.name.first,
                        registration.contact.name.last,
                        registration.contact.mail,
                        registration.contact.tel,
                    ])

                    p_names.append(participant.name)
        data = sorted(data,key=lambda x: (x[0],x[1]))
        sheet = self.gc.open_by_key(self.sheet_ids['registrations'])
        worksheet = sheet.worksheet("Mitglied")
        worksheet.batch_clear(["A3:G1000"])
        worksheet.update("A3",values = data)


    def _dump_zwergerl(self):
        data = []
        for registration in self.registrations:
            for p in registration.participants:
                if p.course in [Course.ZWEGERL,Course.ZWEGERL_SNOWBOARD]:
                    data.append([
                        "ski" if p.course == Course.ZWEGERL else "snowboard",
                        p.name.first,
                        p.name.last,
                        p.age,
                        registration.contact.mail,
                        registration.contact.tel,
                        registration.contact.name.first,
                        registration.contact.name.last,
                        p.notes]
                    )
        sheet = self.gc.open_by_key(self.sheet_ids['registrations'])
        worksheet = sheet.worksheet("Zwergerl")
        worksheet.batch_clear(["A3:I1000"])
        worksheet.update("A3",values = data)
        worksheet.update_acell("G1",len(data))

    def _dump_normal(self):
        data = []
        for registration in self.registrations:
            for p in registration.participants:
                if p.course in [Course.SKI,Course.SNOWBOARD]:
                    data.append([
                        "ski" if p.course == Course.SKI else "snowboard",
                        p.name.first,
                        p.name.last,
                        p.age,
                        registration.contact.mail,
                        registration.contact.tel,
                        registration.contact.name.first,
                        registration.contact.name.last,
                        p.pre_course,
                        p.notes]
                    )
        sheet = self.gc.open_by_key(self.sheet_ids['registrations'])
        worksheet = sheet.worksheet("Kurse")
        worksheet.batch_clear(["A3:J1000"])
        worksheet.update("A3",values = data)
        worksheet.update_acell("G1",len(data))

    def dump_mail_flags(self):
        sheet = self.gc.open_by_key(self.sheet_ids['db'])
        worksheet = sheet.worksheet("Formularantworten")

        cell_values = worksheet.get_all_values()
        ids = list(zip(*cell_values))[-1][1:]
        id_mapping = dict()
        for _id in ids:
            id_mapping[_id] = {"r_cell":f"BF{int(_id)+1}","p_cell":f"BG{int(_id)+1}","price_cell":f"BE{int(_id)+1}"}
        for registration in self.registrations:
            p_mail_sent = "TRUE" if registration.payment_mail_sent else "FALSE"
            r_mail_sent = "TRUE" if registration.registration_mail_sent else "FALSE"
            worksheet.update_acell(id_mapping[registration._id]["r_cell"],r_mail_sent)
            worksheet.update_acell(id_mapping[registration._id]["p_cell"],p_mail_sent)
            worksheet.update_acell(id_mapping[registration._id]["price_cell"],registration.payment.amount)

    def dump_registrations(self):
        self._dump_overview()
        self._dump_paid()
        self._dump_member()
        self._dump_zwergerl()
        self._dump_normal()
        self.dump_mail_flags()

if __name__ == "__main__":
    from gdocs_4_ski_automation.core.factories import GDocsRegistrationFactory




    sheet_ids = {"settings": "1SteMGOoigoPyZMJsB5GG82K4WNh-N2AQIck_xtrmtz8",
                "registrations": "11FLy4qTOScUOLj4xGVPMy12940DsOYz2pmoPDf9pDhA", 
                "db": "1VUuX4UbsWsxd5QUKA7FjsebU2uPTs80dBSSn4Tay_Vk"}

    google_authenticator = GoogleAuthenticatorInterface("data/dependencies/client_secret.json")
    google_client = google_authenticator.gspread
    factory = GDocsRegistrationFactory(sheet_ids,google_client)
    registrations = factory.build_registrations()
    dumper = GDocsDumper(registrations,sheet_ids,google_client)
    dumper.dump_registrations()