export class CellEdit {
    input_types = []; //list of columnnumber and related celledit parameters
    enabled_columns = []; //list of columns that have celledit enabled
    select_options = {}; // dict of columnnumber => dict of value => label
    celltoggle_columns = []

    constructor(table, template, changed_cb) {
        for (let i = 0; i < template.length; i++) {
            let options = [];
            if ("celledit" in template[i]) {
                if (template[i].celledit.type === 'select') {
                    this.select_options[i] = {};
                    template[i].celledit.options.forEach(o => {
                        options.push({value: o[0], display: o[1]});
                        this.select_options[i][o[0]] = o[1];
                    });
                }
                if (template[i].celledit.type === 'toggle') {
                    this.celltoggle_columns.push(i)
                } else {
                    const entry = {column: i, type: template[i].celledit.type, options}
                    this.enabled_columns.push(i);
                    this.input_types.push(entry);
                }
            }
        }
        if (this.input_types.length > 0) {
            this.attach_handler(table, {update_cb: changed_cb, columns: this.enabled_columns, input_types: this.input_types, input_css: "celledit-input"});
        }
    }

    attach_handler = (table, settings) => {
        this.table = table;
        this.settings = settings;
        const _this = this // is required when a function is used iso =>
        if (table != null) {
            $(table.table().body()).on('click', 'td', function () {
                const column_index = table.cell(this).index().column;
                if ((settings.columns && settings.columns.indexOf(column_index) > -1) || (!settings.columns)) {
                    const cell = table.cell(this).node();
                    //If the cell contains an input or select element, ignore additional mouseclicks
                    if (!$(cell).find('input').length && !$(cell).find('select').length) {
                        const old_value = _this.sanitize_value(table.cell(this).data());
                        _this.create_input_element(cell, column_index, old_value);
                        $(cell).on("mouseleave", e => _this.cancel(cell));  // remove edit-element when mouse leaves element
                    }
                }
            });
        }
    }

    create_input_element(target_cell, column_index, old_value) {
        const setting = this.settings.input_types.find(t => t.column === column_index) || null;
        const type = setting !== null ? setting.type.toLowerCase() : null;
        const css = this.settings.input_css || "";
        switch (type) {
            case "select":
                const select = $(`<select class="${css}"></select>`);
                $.each(setting.options, function (index, option) {
                    const selected = old_value === option.value ? "selected" : "";
                    const option_element = $(`<option value=${option.value} ${selected}>${option.display}</option>`);
                    select.append(option_element);
                });
                select.on("change", this.update);
                $(target_cell).html(select);
                break;
            case "text-confirmkey": // text input w/ confirm
            case "int-confirmkey": // integer input w/ confirm
                const input = $(`<input class="${css}" value="${old_value}">`);
                input.on("keyup", e => {
                    if (e.keyCode === 13) this.update(e)
                    else if (e.keyCode === 27) this.cancel(e)
                });
                $(target_cell).html(input);
                input.focus();
                break;
            default:
                break;
        }
    }

    // event points to the element inside the cell, e.g. select
    update = event => {
        const row = this.table.row(event.currentTarget.parentNode.parentNode) // parentNode.parentNode: tr element
        const cell = this.table.cell(event.currentTarget.parentNode) // parentNode: td element
        const old_value = cell.data();
        cell.data(event.currentTarget.value);
        this.settings.update_cb(cell, row, old_value);
        // Get current page and redraw
        let page_index = this.table.page.info().page;
        this.table.page(page_index).draw(false);
    }

    cancel = event => {
        let cell = this.table.cell($(event).parents('td, th'));
        // Set cell to it's original value and redraw
        cell.data(cell.data());
        this.table.draw();
    }

    sanitize_value(value) {
        if (typeof (value) === 'undefined' || value === null || value.length < 1) return "";
        if (isNaN(value)) {/* escape single quote */ value = value.replace(/'/g, "&#39;");}
        return value;
    }
}