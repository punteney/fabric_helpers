=================
Server Setup
=================

Fabric Helpers requires a server to be setup, currently fabric helpers is specific to Ubuntu, and is tested using Ubuntu 10.4, though it should work on any relatively new version of Ubuntu.

A user for this project should also be created on the server. This user should be specific to the project and not an actual person/user if possible. Depending on the project user will most likely need sudo rights to be able to install and restart the needed packages and processes

.. note:: 

    The reason the user should be a generic user specific to the project is that the project files are kept in the created user's home directory. If a user is created who is an actual user then others working on the project would need to have access to the that users home directory, and permissions get more complicated.
