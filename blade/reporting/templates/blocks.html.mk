<%doc>
Copyright (C) 2019 Blu Wireless Ltd.
All Rights Reserved.

This file is part of BLADE.

BLADE is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

BLADE is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
BLADE.  If not, see <https://www.gnu.org/licenses/>.
</%doc>\
<%def name="report_item(item)">\
<%  id = item["path"].strip().replace(" ","-").replace(".","-").lower() %>\
<div "item-${id}" class="container-fluid reportitem" ${'style="display:none;"' if item["priority"] == "DEBUG" else ""}>
    <div class="row header verbosity-${item['priority'].lower()}">
        <div class="col-2">
            [<strong>${item['priority'].upper()}</strong>] ${item['path'].replace('BLADE Report.','')}
        </div>
        <div class="col-10">${item['title']}</div>
    </div>
    <div class="row header datetime verbosity-${item['priority'].lower()}">
        <div class="col-2">${item['date']}</div>
        <div class="col-10"></div>
    </div>
%if 'body' in item and item['body'] and len(item['body'].strip()) > 0:
    <div class="row body">
        <div class="col-12">
            <div class="expander">
                <a href="#item-${id}" class="bodyexpand">Expand message...</a>
            </div>
            <pre class="hidden">${item['body']}</pre>
        </div>
    </div>
%endif
</div>
</%def>\

<%def name="category(cat)">\
%if len(cat['contents']) > 0 or len(cat['categories']) > 0:
<h4>${cat['title']}</h4>
<div class="container-fluid reportcategory rounded p-2">
    %for item in cat['contents']:
<%      report_item(item) %>\
    %endfor
    %for item in cat['categories']:
<%      category(item) %>\
    %endfor
</div>
%endif
</%def>\
