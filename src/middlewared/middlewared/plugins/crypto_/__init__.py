from .utils import CERT_TYPE_EXISTING, DEFAULT_CERT_NAME


async def setup(middleware):
    failure = False
    try:
        system_general_config = await middleware.call('system.general.config')
        system_cert = system_general_config['ui_certificate']
        certs = await middleware.call('datastore.query', 'system.certificate', [], {'prefix': 'cert_'})
    except Exception as e:
        failure = True
        middleware.logger.error(f'Failed to retrieve certificates: {e}', exc_info=True)

    if not failure and (not system_cert or system_cert['id'] not in [c['id'] for c in certs]):
        # create a self signed cert if it doesn't exist and set ui_certificate to it's value
        try:
            if not any(DEFAULT_CERT_NAME == c['name'] for c in certs):
                await middleware.call('certificate.setup_self_signed_cert_for_ui', DEFAULT_CERT_NAME)
                middleware.logger.debug('Default certificate for System created')
            else:
                id = [c['id'] for c in certs if c['name'] == DEFAULT_CERT_NAME][0]
                await middleware.call('certificate.cert_services_validation', id, 'certificate')


                await middleware.call(
                    'datastore.update', 'system.settings', system_general_config['id'], {'stg_guicertificate': id}
                )
        except Exception as e:
            failure = True
            middleware.logger.debug(
                'Failed to set certificate for system.general plugin: %s', e, exc_info=True
            )

    if not failure:
        middleware.logger.debug('Certificate setup for System complete')
