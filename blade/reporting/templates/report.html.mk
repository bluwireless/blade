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
<%namespace name="blocks" file="blocks.html.mk" />\
<html>
<head>
    <title>BLADE Report</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
    <link href="https://fonts.googleapis.com/css?family=Comfortaa" rel="stylesheet">
    <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.7.2/css/all.css" integrity="sha384-fnmOCqbTlWIlj8LyTjo7mOUStjsKC4pOpQbqyi7RrhN7udi9RwhKkMHpvLbHG9Sr" crossorigin="anonymous">
    <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js" integrity="sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/js/bootstrap.min.js" integrity="sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy" crossorigin="anonymous"></script>
    <style type="text/css">
    html, body {
        font-family:'Comfortaa',cursive;
    }
    #main {
        margin-top:30px;
    }
    .reportitem, .reportcategory {
        border:1px solid #CCC;
        margin-bottom:5px;
    }
    .reportitem:last-of-type {
        margin-bottom:0;
    }
    .reportitem .header { }
    .reportitem .header div:first-of-type {
        font-size:12px;
    }
    .reportitem .header.datetime {
        font-size:10px;
        color:#666;
    }
    .reportitem .header.verbosity-debug div:first-of-type {
        background-color:#d6f2f9;
    }
    .reportitem .header.verbosity-info div:first-of-type {
        background-color:#00cbff;
    }
    .report .header.datetime.verbosity-info div:first-of-type {
        color:#FFF;
    }
    .reportitem .header.verbosity-warning div:first-of-type {
        background-color:#ffbf00;
    }
    .reportitem .header.verbosity-error div:first-of-type {
        background-color:#ff2100;
    }
    .reportitem .header.verbosity-error.datetime div:first-of-type {
        color:#FFF !important;
    }
    .reportitem .body {
        border-top:2px solid #AAA;
        padding-top:3px;
    }
    .reportitem .body .expander {
        width:100%;
        text-align:center;
    }
    .hidden {
        display:none;
    }
    </style>
    <script type="text/javascript">
    $(document).ready(function() {
        $('.collapse')
            .on('hide.bs.collapse', function() {
                $(this).parent()
                       .find('.btn .fa')
                       .removeClass('fa-chevron-up')
                       .addClass('fa-chevron-down');
                $(this).parent()
                       .find('.btn span')
                       .html('Show Report');
            })
            .on('show.bs.collapse', function() {
                $(this).parent()
                       .find('.btn .fa')
                       .removeClass('fa-chevron-down')
                       .addClass('fa-chevron-up');
                $(this).parent()
                       .find('.btn span')
                       .html('Hide Report');
            });
        $('.btn.verbosity').on('click', function() {
            var value     = $(this).val();
            var verbosity = value.split(':')[0];
            var state     = value.split(':')[1];
            if (state == 'shown') {
                $('.verbosity-' + verbosity).parent().css('display', 'none');
                $(this).find('i').removeClass('fa-check-square')
                                 .addClass('fa-square');
                $(this).val(verbosity + ':' + 'hidden');
            } else {
                $('.verbosity-' + verbosity).parent().css('display', 'block');
                $(this).find('i').removeClass('fa-square')
                                 .addClass('fa-check-square');
                $(this).val(verbosity + ':' + 'shown');
            }
        });
        $('.bodyexpand').on('click', function() {
            $(this).parent().parent().find('pre.hidden').removeClass('hidden');
            $(this).addClass('hidden');
        });
    });

    </script>
</head>
<body>
    <div id="main" class="container-fluid">
        <div class="row">
            <div class="col"></div>
            <div class="col-10">
                <h1>BLADE Report</h1>

                <div class="container-fluid text-right p-0">
                    <button value="debug:hidden" class="btn btn-sm btn-outline-secondary verbosity">
                        <i class="fa fa-square"></i> Debug Messages
                    </button>
                    <button value="info:shown" class="btn btn-sm btn-outline-primary verbosity">
                        <i class="fa fa-check-square"></i> Info Messages
                    </button>
                    <button value="warning:shown" class="btn btn-sm btn-outline-warning verbosity">
                        <i class="fa fa-check-square"></i> Warning Messages
                    </button>
                    <button value="error:shown" class="btn btn-sm btn-outline-danger verbosity">
                        <i class="fa fa-check-square"></i> Error Messages
                    </button>
                </div>
                <br />
                <div class="accordion">
%for category in report['categories']:
<%  id = category["title"].strip().replace(" ","-").replace(".","-").lower() %>\
                    <div class="card" id="card-${id}">
                        <div class="card-header">
                            <h3 class="mb-0 float-left">${category["title"].replace("_", " ").capitalize()}</h3>
                            <a class="btn btn-sm btn-outline-primary float-right" href="card-${id}" data-toggle="collapse" data-target="#collapse-${id}" aria-expanded="false" aria-controls="collapse-${id}">
                                <i class="fa fa-chevron-down"></i> <span>Show Report</span>
                            </a>
                        </div>
                        <div class="collapse" id="collapse-${id}">
                            <div class="card-body">
<%                              blocks.category(category) %>\
                            </div>
                        </div>
                    </div>
%endfor
                </div>
            </div>
            <div class="col"></div>
        </div>
    </div>
</body>
</html>
