FROM python:3.9-slim AS memtab_container

# Install uv
RUN pip install uv

WORKDIR /code
# Copy the entire project into the container
COPY src /code/src/
COPY pyproject.toml uv.lock README.rst /code/

RUN apt update -y

# this will also install gcc and nm for x86, in case you want to run memtab on a binary for the host system
# it needs to be run prior to the uv sync call, because gcc and g++ are used by some of the dependencies
RUN apt install wget binutils build-essential ca-certificates clang -y

# Install memtab package via uv
RUN uv python install
RUN uv sync

# now download the arm cross-compiler
RUN wget https://developer.arm.com/-/media/Files/downloads/gnu/14.2.rel1/binrel/arm-gnu-toolchain-14.2.rel1-x86_64-arm-none-eabi.tar.xz
RUN tar xf arm-gnu-toolchain-14.2.rel1-x86_64-arm-none-eabi.tar.xz
RUN rm arm-gnu-toolchain-14.2.rel1-x86_64-arm-none-eabi.tar.xz
ENV PATH="$PATH:/code/arm-gnu-toolchain-14.2.rel1-x86_64-arm-none-eabi/bin"

# download the zephyr SDK
RUN wget https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v0.16.5/toolchain_linux-x86_64_arm-zephyr-eabi.tar.xz
RUN tar xf toolchain_linux-x86_64_arm-zephyr-eabi.tar.xz
RUN rm toolchain_linux-x86_64_arm-zephyr-eabi.tar.xz
ENV PATH="$PATH:/code/arm-zephyr-eabi/bin"

# Download the xtensa esp elf SDK
RUN wget https://github.com/espressif/crosstool-NG/releases/download/esp-14.2.0_20241119/xtensa-esp-elf-14.2.0_20241119-x86_64-linux-gnu.tar.xz
RUN tar xf xtensa-esp-elf-14.2.0_20241119-x86_64-linux-gnu.tar.xz
RUN rm xtensa-esp-elf-14.2.0_20241119-x86_64-linux-gnu.tar.xz
ENV PATH="$PATH:/code/xtensa-esp-elf/bin"

# Set the entry point to the memtab command
ENTRYPOINT ["uv", "run", "memtab"]

# Pass all arguments to memtab
CMD ["--help"]
