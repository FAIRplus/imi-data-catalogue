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

(function ($) {
    $.fn.extend({
        select2_sortable: function (options) {
            var select = $(this);
            $(select).select2(
                options
            );
            var ul = $(select).next('.select2-container').first('ul.select2-selection__rendered');
            ul.sortable({
                placeholder: 'ui-state-highlight',
                forcePlaceholderSize: true,
                items: 'li:not(.select2-search__field)',
                tolerance: 'pointer',
                stop: function () {
                    $($(ul).find('.select2-selection__choice').get().reverse()).each(function () {
                        var id = $(this).data('data').id;
                        var option = select.find('option[value="' + id + '"]')[0];
                        $(select).prepend(option);
                    });
                }
            });
        }
    });
}(jQuery));