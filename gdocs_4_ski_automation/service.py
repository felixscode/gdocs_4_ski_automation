from gdocs_4_ski_automation.core.factories import GDocsRegistrationFactory

def run(secrets_path, gdocs_ids):
    factory = GDocsRegistrationFactory(secrets_path, gdocs_ids)
    registrations = factory.build_registrations()
    