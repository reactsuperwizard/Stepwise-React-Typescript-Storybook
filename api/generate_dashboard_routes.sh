#!/bin/bash

set -o errexit
set -o nounset

cp ../dashboard/src/routes/index.ts apps/core/dashboard.py
# convert enums
sed -i -E 's/^export enum (\w+)\s*\{/class \1:/;' apps/core/dashboard.py
# convert dict to class
sed -i 's/const routes = {/class DashboardRoutes:/;' apps/core/dashboard.py
sed -i -E 's/^}//;' apps/core/dashboard.py
sed -i -E 's/,$//;' apps/core/dashboard.py
sed -i -E 's/export default routes//;' apps/core/dashboard.py
sed -i -E 's/;//;' apps/core/dashboard.py
# convert keys to fields
sed -i -E 's/^(\s+)(\w+?):/\1\2 =/;' apps/core/dashboard.py
# remove new lines
sed -i -E ':a;N;$!ba;s/=\n\s+/= /g;' apps/core/dashboard.py
# fix template variables
sed -i -E 's/\/:(\w+?)/\/{\1}/g;' apps/core/dashboard.py
# use 4 spaces to indent code
sed -i -E 's/^\s{2}/    /g;' apps/core/dashboard.py

echo "Generated dashboard routes"