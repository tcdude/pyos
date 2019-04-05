#!/usr/bin/env bash

# Modify to match file names, keystore location, key alias and keystore password
APKUNSIGNED="pyos-$1-beta-release-unsigned.apk"
APKSIGNED="pyos-$1-beta-release-signed.apk"
KEYSTORE="/foo/bar/pyos.keystore"
KEYALIAS="pyos-key"
STOREPASS="PASSWORD"
BUILDTOOLSDIR="/home/tc/android/SDK/build-tools/28.0.3/"

echo "deleting output file"
rm "$APKSIGNED"
echo "signing APK"
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore "$KEYSTORE" \
    "$APKUNSIGNED" ${KEYALIAS} -storepass ${STOREPASS}
echo "zipaling APK"
${BUILDTOOLSDIR}zipalign -v 4 "$APKUNSIGNED" "$APKSIGNED"
echo "verifying APK"
${BUILDTOOLSDIR}apksigner verify "$APKSIGNED"
echo "done"
