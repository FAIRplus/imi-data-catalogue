/*
 * DataCatalog
 * Copyright (C) 2020  University of Luxembourg
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

var csrftoken = $('meta[name=csrf-token]').attr('content');

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken)
        }
    }
});

$.extend(
    {
        redirectPost: function (location, args) {
            var form = $('<form>');
            form.attr("method", "post");
            form.attr("action", location);

            $.each(args, function (key, value) {
                var field = $('<input>');

                field.attr("type", "hidden");
                field.attr("name", key);
                field.attr("value", value);

                form.append(field);
            });
            var field = $('<input type="hidden" name="csrf_token">').attr('value', csrftoken);
            form.append(field);
            $(form).appendTo('body').submit();
        }
    });


$(document).ready(function () {

    $.material.init();
    $('[data-toggle="tooltip"]').tooltip();
    $('#query').change(function () {
        $('#sort_by').val('');
    });

    $('.start-collapsed').collapse('hide');
    var hash = window.location.hash;
    if (hash) {
        $('div' + hash).collapse('show');

    } else {
        $('.start-visible').collapse('show');
    }
    var fairPlusStamp = $(".fairResultsStamp");
    if (fairPlusStamp) {
        var expandId = fairPlusStamp.data('expand');
        if (expandId) {
            fairPlusStamp.click(function () {
                $('div#' + expandId).collapse('show');
            });
        }
    }
})
;