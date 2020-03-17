#!/usr/bin/env bash

# Modify to match file names, keystore location, key alias and keystore password
APKUNSIGNED32="pyos-beta__armeabi-v7a-release-unsigned-$1-.apk"
APKSIGNED32="pyos-beta__armeabi-v7a-release-signed-$1-.apk"
APKUNSIGNED64="pyos-beta__arm64-v8a-release-unsigned-$1-.apk"
APKSIGNED64="pyos-beta__arm64-v8a-release-signed-$1-.apk"
KEYSTORE="/foo/bar/pyos.keystore"
KEYALIAS="pyos-key"
STOREPASS="PASSWORD"
BUILDTOOLSDIR="/home/tc/android/SDK/build-tools/28.0.3/"

echo "32bit -> deleting output file"
rm "$APKSIGNED32"
echo "signing APK"
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore "$KEYSTORE" \
    "$APKUNSIGNED32" ${KEYALIAS} -storepass ${STOREPASS}
echo "zipaling APK"
${BUILDTOOLSDIR}zipalign -v 4 "$APKUNSIGNED32" "$APKSIGNED32"
echo "verifying APK"
${BUILDTOOLSDIR}apksigner verify "$APKSIGNED32"

echo "64bit -> deleting output file"
rm "$APKSIGNED64"
echo "signing APK"
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore "$KEYSTORE" \
    "$APKUNSIGNED64" ${KEYALIAS} -storepass ${STOREPASS}
echo "zipaling APK"
${BUILDTOOLSDIR}zipalign -v 4 "$APKUNSIGNED64" "$APKSIGNED64"
echo "verifying APK"
${BUILDTOOLSDIR}apksigner verify "$APKSIGNED64"

echo "done"
