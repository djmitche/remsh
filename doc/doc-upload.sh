#! /bin/sh

VERSION=`cat VERSION`
REV=`git rev-parse HEAD`

if test -z "$REV" -o -z "$VERSION"; then
    echo "bailing out"
    exit 1
fi

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

    # make sure the versions list in index.html is up to date
    export VERSLIST=`cd docs; ls -1|sed 's!^\(.*\)$!<li><a class="reference" href="docs/\1">remsh-\1</a></li>!'`
    awk  '
BEGIN { doprint=1; }
$0 ~ /<!-- VERSLIST -->/ { print; doprint = 0; print ENVIRON["VERSLIST"]; }
$0 ~ /<!-- END-VERSLIST -->/ { doprint = 1; }
doprint == 1 { print }' < index.html > index.tmp || exit 1
    mv index.tmp index.html

    # github doesn't allow directories beginning with a _, so we rename and move stuff around
    # (note this assumes GNU sed)
    mv docs/$VERSION/_static docs/$VERSION/static || exit 1
    find docs/$VERSION -type f -exec sed -i -e 's!_static/!static/!g' \{} \; || exit 1
    git add docs/$VERSION || exit 1
    git commit -m "upload-docs - $REV" || exit 1
    git push origin gh-pages || exit 1
)
