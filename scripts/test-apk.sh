#!/usr/bin/env bash

# Modify to reflect package name
PACKAGE="org.test.app"

echo "Trying to uninstall ${PACKAGE}"
adb uninstall ${PACKAGE}
echo "Trying to install $1"
adb install $1
sleep 0.2
echo "Trying to launch ${PACKAGE}"
adb shell am start -n ${PACKAGE}/org.kivy.android.PythonActivity
echo "Done"
