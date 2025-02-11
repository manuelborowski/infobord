import {base_init} from "../base.js";
import {fetch_delete, fetch_post} from "../common/common.js";

const action_buttons = ` <a type="button" class="btn-item-delete btn btn-success"><i class="fa-solid fa-xmark" title="Lijn verwijderen"></i></a></div> `

const table_meta = [
    {value: action_buttons, label: "Actie", source: "value"},
    {value: "lesuur", label: "Lesuur", source: "data", type: "int", size: 3},
    {value: "leerkracht", label: "Te vervangen", source: "data", size: 20},
    {value: "klas", label: "Klas", source: "data", size: 10},
    {value: "info", label: "Taak/Toets", source: "data", size: 15},
    {value: "locatie", label: "Lokaal", source: "data", size: 15},
    {value: "vervanger", label: "Vervanger", source: "data", size: 20},
]

const __draw_table = (data, nbr_rows = 20, add_to_table = false) => {
    const info_table = document.getElementById("info-table");
    let table = null;
    if (add_to_table) {
        table = info_table.querySelector("table");
    } else {
        info_table.innerHTML = "";
        table = document.createElement("table");
        info_table.appendChild(table);
        const tr = document.createElement("tr");
        table.appendChild(tr);
        for (const column of table_meta) {
            const th = document.createElement("th");
            tr.appendChild(th);
            th.innerHTML = column.label;
        }
    }
    if (data.length > 0) { // use items from database
        for (const item of data) {
            const tr = document.createElement("tr");
            table.appendChild(tr);
            tr.dataset["id"] = item.id;
            for (const column of table_meta) {
                const td = document.createElement("td");
                tr.appendChild(td);
                const type = "type" in column ? column.type : "string";
                if (column.source === "value") {
                    td.innerHTML = column.value;
                } else {
                    const input = document.createElement("input");
                    td.appendChild(input);
                    input.dataset.field = column.value;
                    input.dataset.type = type;
                    input.value = item[column.value];
                    input.size = column.size;
                }
            }
        }
    } else { // empty table
        for (let i = 0; i < nbr_rows; i++) {
            const tr = document.createElement("tr");
            table.appendChild(tr);
            tr.dataset["id"] = i;
            for (const column of table_meta) {
                const td = document.createElement("td");
                tr.appendChild(td);
                const type = "type" in column ? column.type : "string";
                if (column.source === "value") {
                    td.innerHTML = column.value;
                } else {
                    const input = document.createElement("input");
                    td.appendChild(input);
                    input.dataset.field = column.value;
                    input.dataset.type = type;
                    input.value = "";
                    input.size = column.size;
                }
            }

        }
    }
    info_table.querySelectorAll(".btn-item-delete").forEach(r => r.addEventListener("click", e => {
        const tr = e.target.closest("tr");
        tr.remove();
    }));
    info_table.querySelectorAll("input").forEach(e => e.addEventListener("input", () => document.getElementById("info-save").classList.add("blink-button")));
}

const __info_save = async () => {
    const rows = document.querySelectorAll('[data-id]');
    let data = []
    for (const row of rows) {
        let item = {school: global_data.school};
        const columns = row.querySelectorAll("[data-field]");
        for (const column of columns) {
            const field = column.dataset.field;
            if (column.dataset.type === "int") {
                column.value = column.value === "" ? 0 : column.value;
                const value = parseInt(column.value);
                if (isNaN(value)) {
                    const column_meta = table_meta.filter(i => i.value === column.dataset.field)[0];
                    bootbox.alert(`Opgepast, in kolom "${column_meta.label}" mag alleen een getal staan`)
                    return
                }
                item[field] = value;
            } else
                item[field] = column.value
        }
        if (item.lesuur > 0) data.push(item);
    }
    const resp = await fetch_post("infobord.edit", data, {school: global_data.school});
    if (resp) __draw_table(resp.data);
    document.getElementById("info-save").classList.remove("blink-button");

}

const __info_delete = async () => {
    bootbox.confirm({
        size: "small",
        message: "U gaat alle lijnen wissen, zeker?",
        callback: async result => {
            if (result) {
                const resp = await fetch_delete("infobord.edit", {school: global_data.school})
                if (resp) __draw_table([]);
            }
        }
    });
}

const __info_sort = async () => {
    const rows = document.querySelectorAll('[data-id]');
    let data = []
    for (const row of rows) {
        let item = {school: global_data.school};
        const columns = row.querySelectorAll("[data-field]");
        for (const column of columns) {
            const field = column.dataset.field;
            if (column.dataset.type === "int") {
                column.value = column.value === "" ? 0 : column.value;
                const value = parseInt(column.value);
                if (isNaN(value)) {
                    const column_meta = table_meta.filter(i => i.value === column.dataset.field)[0];
                    bootbox.alert(`Opgepast, in kolom "${column_meta.label}" mag alleen een getal staan`)
                    return
                }
                item[field] = value;
            } else
                item[field] = column.value
        }
        if (item.lesuur > 0) data.push(item);
    }
    data.sort((a, b) => a.lesuur - b.lesuur);
    __draw_table(data)
}

const __info_add_rows = nbr => {
    __draw_table([], nbr, true);
}

const button_menu_items = [
    {
        type: 'button',
        id: 'info-save',
        label: 'Bewaar',
        cb: () => __info_save()
    },
    {
        type: 'button',
        id: 'info-sort',
        label: 'Sorteer',
        cb: () => __info_sort()
    },
    {
        type: 'button',
        id: 'info-delete',
        label: 'Leegmaken',
        cb: () => __info_delete()
    },
    {
        type: 'button',
        id: 'info-add',
        label: '+5 rijen',
        cb: () => __info_add_rows(5)
    },
]

$(document).ready(function () {
    if (current_user.level < 3)
        base_init({});
    else
        base_init({button_menu_items});
    __draw_table(global_data.info);
});

