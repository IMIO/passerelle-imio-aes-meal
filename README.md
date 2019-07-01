Passerelle connector : Import aes meal to use it in specific form of the parent portal
=============================================================================================

Installation
------------

 - add to Passerelle installed apps settings:
   INSTALLED_APPS += ('passerelle_imio_aes_meal',)
   TENANT_APPS += ('passerelle_imio_aes_meal',)


 - enable module:
   PASSERELLE_APP_PASSERELLE_IMIO_AES_MEAL_ENABLED = True


Usage
-----

 - create and configure new connector
   - Title/description: whatever you want
   - URL: https://e-services.liege.be:8443/
   - Certificate check: uncheck if the service has no valid certificate

 - test service by clicking on the available links
   - the /voies/ endpoint may take some time as it will query for everything
     (but will be cut at 51 items)
   - the /voies/?q=... endoint is set with an example string, feel free to
     change it.


Usage in w.c.s.
---------------

 - configure a multiselect list field


Usage of 'import_json' destination and motivation in command line
-----------------------------------------------------------------
with user passerelle :
- sudo -u passerelle passerelle-manage tenant_command import_site -d local-passerelle.example.net [JSON_FILE]
