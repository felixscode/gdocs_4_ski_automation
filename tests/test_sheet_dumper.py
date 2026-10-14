from types import SimpleNamespace
from unittest.mock import MagicMock

from gdocs_4_ski_automation.core.sheet_dumper import GDocsDumper


def _registration(_id: int, amount: float, r_sent: bool, p_sent: bool):
    return SimpleNamespace(
        _id=_id,
        payment=SimpleNamespace(amount=amount),
        registration_mail_sent=r_sent,
        payment_mail_sent=p_sent,
    )


def test_dump_mail_flags_writes_to_registration_rows() -> None:
    """Flags land in each registration's own row, even with empty rows in between."""
    registrations = [_registration(1, 200, True, False), _registration(69, 395, True, False)]
    dumper = GDocsDumper(registrations, {"db": "db-id"}, MagicMock())
    worksheet = dumper.gc.open_by_key.return_value.worksheet.return_value
    dumper._batch_update_with_retry = MagicMock()

    dumper.dump_mail_flags()

    dumper._batch_update_with_retry.assert_called_once_with(
        worksheet,
        [
            {"range": "BE2:BH2", "values": [[200, "TRUE", "FALSE", "1"]]},
            {"range": "BE70:BH70", "values": [[395, "TRUE", "FALSE", "69"]]},
        ],
    )
