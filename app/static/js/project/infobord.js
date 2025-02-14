import {base_init} from "../base.js";
import {fetch_delete, fetch_get, fetch_post} from "../common/common.js";

const action_buttons = ` <a type="button" class="btn-item-delete btn btn-success"><i class="fa-solid fa-xmark" title="Lijn verwijderen"></i></a></div> `
const info_date = document.getElementById("info-date");

let vervangers = {};
const __draw_table = (data = [], nbr_rows = 20, add_to_table = false) => {
    const __lesuur_changed = e => {
        const select = e.target.closest("tr").querySelector("[data-type=vervanger]");
        if (e.target.value in vervangers) {
            select.innerHTML = "";
            select.add(new Option("", "", true, true));
            vervangers[e.target.value].forEach(i => select.add(new Option(i, i)));
            select.hidden = false;
        } else {
            select.hidden = true;
        }
    }
    const __vervanger_changed = e => {
        const value = e.target.value;
        const vervanger_field = e.target.closest("tr").querySelector("[data-field=vervanger]");
        vervanger_field.value = value;
    }
    const table_meta = [
        {value: action_buttons, label: "Actie", source: "value"},
        {value: "lesuur", label: "Lesuur", source: "data", type: "int", size: 3, cb: __lesuur_changed},
        {value: "leerkracht", label: "Te vervangen", source: "data", size: 20},
        {value: "klas", label: "Klas", source: "data", size: 10},
        {value: "info", label: "Taak/Toets", source: "data", size: 15},
        {value: "locatie", label: "Lokaal", source: "data", size: 15},
        {value: "vervanger", label: "Vervanger", source: "data", size: 20},
        {value: "vervanger", label: "Selecteer", source: "vervanger", size: 20, cb: __vervanger_changed},
    ]
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
                } else if (column.source === "vervanger") {
                    const select = document.createElement("select")
                    td.appendChild(select);
                    select.dataset.type = "vervanger"
                    select.hidden = true;
                    if ("cb" in column) select.addEventListener("change", column.cb);
                } else {
                    const input = document.createElement("input");
                    td.appendChild(input);
                    input.dataset.field = column.value;
                    input.dataset.type = type;
                    input.value = item[column.value];
                    input.size = column.size;
                    if ("cb" in column) input.addEventListener("input", column.cb);
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
                } else if (column.source === "vervanger") {
                    const select = document.createElement("select")
                    td.appendChild(select);
                    select.dataset.type = "vervanger"
                    select.hidden = true;
                    if ("cb" in column) select.addEventListener("change", column.cb);
                } else {
                    const input = document.createElement("input");
                    td.appendChild(input);
                    input.dataset.field = column.value;
                    input.dataset.type = type;
                    input.value = "";
                    input.size = column.size;
                    if ("cb" in column) input.addEventListener("input", column.cb);
                }
            }

        }
    }
    const rows = Array.from(table.querySelectorAll("tr"));
    rows.shift();
    for (const row of rows) {
        for (const column of table_meta) {
            if (column.source === "data" && "cb" in column) {
                row.querySelector(`td [data-field=${column.value}]`).dispatchEvent(new Event("input"));

            }
        }
    }

    info_table.querySelectorAll(".btn-item-delete").forEach(r => r.addEventListener("click", e => {
        const tr = e.target.closest("tr");
        tr.remove();
    }));
    info_table.querySelectorAll("input").forEach(e => e.addEventListener("input", () => document.getElementById("info-save").classList.add("blink-button")));
}

const __init_select_date = () => {
    const dagen = ["", "maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", ""];

    info_date.innerHTML = "";
    let date = new Date();

    for (let dag = 0; dag < 21; dag++) {
        let day_of_week = date.getDay() % 7;
        if (dagen[day_of_week] !== "") {
            info_date.add(new Option(`${dag === 0 ? "Vandaag" : dagen[day_of_week]} (${date.toISOString().split("T")[0]})`, date.toISOString().split("T")[0], dag === 0, dag === 0));
            if (day_of_week === 5) {
                const option = new Option("-------------------------", null);
                option.disabled = true;
                info_date.add(option);
            }
        }
        date.setDate(date.getDate() + 1);
    }
    info_date.addEventListener("change", async e => {
        const resp = await fetch_get("infobord.infobord", {school: global_data.school, datum: e.target.value});
        if (resp) {
            resp.data.sort((a, b) => a.lesuur - b.lesuur);
            // prepare list of vervangers
            if ("vervangers" in resp && resp.vervangers.length > 0) {
                for (const v of resp.vervangers) {
                    if (v.lesuur in vervangers)
                        vervangers[v.lesuur].push(v.vervanger);
                    else
                        vervangers[v.lesuur] = [v.vervanger];
                }
            }
            for (const [l, v] of Object.entries(vervangers)) vervangers[l] = [...new Set(v.sort())]
            __draw_table(resp.data);
        }
    });
    info_date.dispatchEvent(new Event("change")); // trigger first load
}

const __info_save = async () => {
    const rows = document.querySelectorAll('[data-id]');
    const date = document.getElementById("info-date").value;
    let data = []
    for (const row of rows) {
        let item = {school: global_data.school, datum: `${date}`};
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
    const resp = await fetch_post("infobord.infobord", data, {school: global_data.school, datum: info_date.value});
    if (resp) __draw_table(resp.data);
    document.getElementById("info-save").classList.remove("blink-button");
}

const __info_delete = async () => {
    bootbox.confirm({
        size: "small",
        message: "U gaat alle lijnen wissen, zeker?",
        callback: async result => {
            if (result) {
                const resp = await fetch_delete("infobord.infobord", {school: global_data.school, datum: info_date.value})
                    if (resp) __draw_table();
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
    __init_select_date();

    document.getElementById("preview").addEventListener("click", () => {
        window.open(window.location.origin + "/infobordview?school=" + global_data.school + "&fontsize=x-large", "_blank");
    });
});

