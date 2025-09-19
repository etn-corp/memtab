Docker
======

As referenced in a few other sections, this tool depends on the `objdump` and `readelf` tools to get information about the ELF file.
These tools are not available on by default on Windows, and the non-x86 versions are not installed by default on Linux, so it requires
some system configuration in order to make the memory tabulator functional.  One way we support this is via a docker container to run the memory tabulator.

The root of this repository contains a `Dockerfile`, which creates a docker container that has all the necessary tools to run the memory tabulator, such as the `arm-none-eabi` tools.

There is a github action that publishes an updated docker image whenever there is a push to the main branch.
You can install the docker container to your machine, thus avoiding having to install the `arm-none-eabi` tools, by running the following command:

.. code-block:: console

   docker pull ghcr.io/etn-corp/memtab/memtab-main:latest

More documentation on this can be found `here <https://github.com/etn-corp/memtab/pkgs/container/memtab%2Fmemtab-main>`_, including description of how to authenticate in the "Learn more about packages" link.
