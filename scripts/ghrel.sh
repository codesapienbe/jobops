#!/bin/bash

VERSION=$1

if [ -z "$VERSION" ]; then
    # JOBOPS-YY.MM.DD
    version_number=$(date +%y.%m.%d)
    VERSION="v$version_number"
fi

git commit -am "🚀 v$VERSION"
git tag v$VERSION
git push origin main --tags --force

