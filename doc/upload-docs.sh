#! /bin/sh

VERSION=`cat ../VERSION`

(
cd /tmp
if ! test -d remsh-docs-tmp/remsh; then
    rm -rf remsh-docs-tmp || exit 1
    mkdir remsh-docs-tmp || exit 1
    cd remsh-docs-tmp || exit 1
    git clone git@github.com:djmitche/remsh.git || exit 1
    cd remsh
    git checkout -b gh-pages origin/gh-pages
fi

cd /tmp/remsh-docs-tmp/remsh || exit 1
git checkout gh-pages || exit 1

if test -d docs/$VERSION; then git rm -rf docs/$VERSION || rm -rf docs/$VERSION; fi
mkdir -p docs/$VERSION || exit 1
) || exit 1

sphinx-build -E -a -d /tmp/remsh-docs-tmp/doctrees . /tmp/remsh-docs-tmp/remsh/docs/$VERSION || exit 1

(
cd /tmp/remsh-docs-tmp/remsh || exit 1

# github doesn't allow directories beginning with a _, so we rename and move stuff around
mv docs/$VERSION/_static docs/$VERSION/static || exit 1
find docs/$VERSION -type f -exec sed -i -e 's!_static/!static/!g' \{} \;
git add docs/$VERSION
)
echo "NOW, MANUALLY:"
echo "pushd /tmp/remsh-docs-tmp/remsh"
echo "git commit WHATEVER"
echo "git push origin gh-pages"
