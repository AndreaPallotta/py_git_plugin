#!/usr/bin/env bash

EXE_PATH="./dist/gitex.exe"
if [ ! -f "$EXE_PATH" ]; then
    echo "Error: gitex.exe not found at $EXE_PATH."
    exit 1
fi

sudo cp "$EXE_PATH" /usr/bin/gitex
sudo chmod +x /usr/bin/gitex

echo "Setup completed."