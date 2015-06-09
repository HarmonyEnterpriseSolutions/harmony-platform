@recho off

REM Enter keystore password:  storepass
REM What is your first and last name?
REM   [Unknown]:  Oleg Noga
REM What is the name of your organizational unit?
REM   [Unknown]:  IT
REM What is the name of your organization?
REM   [Unknown]:  Abrisola
REM What is the name of your City or Locality?
REM   [Unknown]:  Kyiv
REM What is the name of your State or Province?
REM   [Unknown]:  Kyiv
REM What is the two-letter country code for this unit?
REM   [Unknown]:  UA
REM Is CN=Oleg Noga, OU=IT, O=Abrisola, L=Kyiv, ST=Kyiv, C=UA correct?
REM   [no]:  yes

keytool -genkey -keyalg rsa -alias abrisola