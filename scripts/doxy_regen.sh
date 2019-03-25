#!/bin/sh

# File:        doxy_regen.sh
# Date:        3/20/2019
# Site:        http://doxy.segs.io/
# Author:      Lloyd Dilley
# Description: doxy_regen.sh is intended for use with cron to rebuild Doxygen documentation
#              automatically at specific intervals.
# Example:     0 0 * * * /usr/local/bin/doxy_regen.sh > /dev/null 2>&1
#
# License:     Copyright (c) 2019 SEGS Project (http://www.segs.io/)
#              All rights reserved.
#
#              Redistribution and use in source and binary forms, with or without
#              modification, are permitted provided that the following conditions are met:
#                  * Redistributions of source code must retain the above copyright
#                    notice, this list of conditions and the following disclaimer.
#                  * Redistributions in binary form must reproduce the above copyright
#                    notice, this list of conditions and the following disclaimer in the
#                    documentation and/or other materials provided with the distribution.
#                  * Neither the name of the copyright holders nor the names of its
#                    contributors may be used to endorse or promote products derived
#                    from this software without specific prior written permission.
#
#              THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#              ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#              WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#              DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS OR CONTRIBUTORS BE LIABLE
#              FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#              DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#              SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#              CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#              OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#              OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Uncomment to debug execution
#set -x

# Configurables
REPO_URL="https://github.com/Segs/Segs"
REPO_DIR="Segs"
REPO_BRANCH="develop"
LOGO_FILE="images/segs_logo.jpg"
DOXY_FILE="Doxyfile"
DOXY_DEST="/var/www/doxy"
DOXY_LOG="segs_doxy.log"

# Clone repo if it does not exist
if [ ! -d "${REPO_DIR}" ]; then
  git clone "${REPO_URL}"
fi

if [ -d "${REPO_DIR}" ]; then
  cd "${REPO_DIR}"

  # Update repo
  git remote update

  # Only generate documentation if repo changes detected
  if ! git diff-index --quiet HEAD --; then
    # Update clone and throw away any local changes for good measure
    git fetch --all && git reset --hard origin/"${REPO_BRANCH}"

    # Get version information
    SEGS_VERSION=`grep "#define SEGS_VERSION" include/Version.h | awk '{print $3}' | sed -e 's/^"//' -e 's/"$//'`
    GIT_BRANCH=`git branch | awk '{print $2}'`
    GIT_HASH=`git rev-parse --short HEAD`
    FULL_VERSION="${SEGS_VERSION}-${GIT_BRANCH} [${GIT_HASH}]"

    # Inject version into Doxyfile prior to generation
    sed -i "s/\(^PROJECT_NUMBER\)\(.*\)/\1 = \"${FULL_VERSION}\"/" "${DOXY_FILE}"

    # Copy images into place so they are available prior to generation
    if [ -f ../"${LOGO_FILE}" ]; then
      cp ../"${LOGO_FILE}" .
    fi
    mkdir images
    cp ../images/segs*dbschema.png images

    # Generate documentation
    doxygen

    # Move new documentation into place and archive previous
    if [ -d "${DOXY_DEST}.old" ]; then
      rm -rf "${DOXY_DEST}".old
    fi
    mv "${DOXY_DEST}" "${DOXY_DEST}".old
    mkdir -p "${DOXY_DEST}"/images/dbschema
    if [ -d "${DOXY_DEST}" ]; then
      cp -Rp doxygen/html/* "${DOXY_DEST}"
      cp ../images/segs*dbschema.png "${DOXY_DEST}"/images/dbschema
    else
      echo "Unable to create ${DOXY_DEST} directory!"
      exit 1
    fi

    # Clean up
    rm -rf doxygen
    rm -f "${LOGO_FILE}"
    if [ -f "${DOXY_LOG}" ]; then
      mv "${DOXY_LOG}" ..
    fi

    # Update clone and throw away any local changes again
    git fetch --all && git reset --hard origin/"${REPO_BRANCH}"
  else
    echo "No repo changes detected."
    exit 0
  fi
else
  echo "${REPO_DIR} repo directory does not exist!"
  exit 1
fi
