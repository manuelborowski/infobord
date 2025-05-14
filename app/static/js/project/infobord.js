import {base_init} from "../base.js";
import {fetch_delete, fetch_get, fetch_post, fetch_update} from "../common/common.js";
import {ContextMenu} from "../common/context_menu.js";

let meta = await fetch_get("infobord.meta", {school: global_data.school});
let info = null;
const info_date_select = document.getElementById("info-date");

class ExtraInfo {
    static quill_toolbar_options = [
        ['bold', 'italic', 'underline', 'strike'],        // toggled buttons
        ['blockquote', 'code-block'],
        ['link', 'image', 'video', 'formula'],

        [{'header': 1}, {'header': 2}],               // custom button values
        [{'list': 'ordered'}, {'list': 'bullet'}, {'list': 'check'}],
        [{'script': 'sub'}, {'script': 'super'}],      // superscript/subscript
        [{'indent': '-1'}, {'indent': '+1'}],          // outdent/indent
        [{'direction': 'rtl'}],                         // text direction

        [{'size': ['small', false, 'large', 'huge']}],  // custom dropdown
        [{'header': [1, 2, 3, 4, 5, 6, false]}],

        [{'color': []}, {'background': []}],          // dropdown with defaults from theme
        [{'font': []}],
        [{'align': []}],

        ['clean']                                         // remove formatting button
    ];
    static location_options = [
        {value: "none-0", label: "Niet"},
        {value: "left-0", label: "Links"},
        {value: "top-0", label: "Bovenaan"},
        {value: "lesuur-1", label: "In lesuur 1"},
        {value: "lesuur-2", label: "In lesuur 2"},
        {value: "lesuur-3", label: "In lesuur 3"},
        {value: "lesuur-4", label: "In lesuur 4"},
        {value: "lesuur-5", label: "In lesuur 5"},
        {value: "lesuur-6", label: "In lesuur 6"},
        {value: "lesuur-7", label: "In lesuur 7"},
        {value: "lesuur-8", label: "In lesuur 8"},
        {value: "lesuur-9", label: "In lesuur 9"},
    ]

    constructor(info_save_btn) {
        this.quill = new Quill(document.getElementById("extra-info"), {modules: {toolbar: ExtraInfo.quill_toolbar_options}, theme: 'snow', placeholder: "Typ hier je boodschap"});
        this.__location = document.getElementById("extra-info-location");
        this.__location.innerHTML = "";
        ExtraInfo.location_options.forEach(o => this.__location.add(new Option(o.label, o.value)));
        this.quill.on("text-change", () => this.info_save_btn.classList.add("blink-button"));
        this.__location.addEventListener("input", () => this.info_save_btn.classList.add("blink-button"));
        this.info_save_btn = info_save_btn;

    }

    content_get() {
        return this.quill.root.innerHTML;
    }

    async content_set(msg) {
        // disable the eventhandler temporarily else the save button starts blinking when the page is loaded
        this.quill.off("text-change");
        await this.quill.clipboard.dangerouslyPasteHTML(msg);
        this.quill.on("text-change", () => this.info_save_btn.classList.add("blink-button"));
    }

    id_get() {
        return document.getElementById("extra-info").dataset.id;
    }

    id_set(id) {
        document.getElementById("extra-info").dataset.id = id;
    }

    location_get() {
        return this.__location.value
    }

    location_set(location) {
        this.__location.value = location;

    }
}

class Info {
    static info_table_tbl = document.getElementById("info-table");

    vervangers = {};

    constructor(info_save_btn) {
        this.info_save_btn = info_save_btn;
        this.info_delete = [];
        this.extra_info = new ExtraInfo(info_save_btn);
        this.id_ctr = -1;
    }

    draw = (data = [], nbr_rows = 20, add_to_table = false) => {
        const action_buttons = ` <a type="button" class="btn-item-delete btn btn-success"><i class="fa-solid fa-xmark" title="Lijn verwijderen"></i></a></div> `
        const __draw_row = (item) => {
            const tr = document.createElement("tr");
            table.appendChild(tr);
            tr.dataset["id"] = item.id;
            for (const field of meta.school_info.fields) {
                const column = meta.field_info[field];
                const td = document.createElement("td");
                tr.appendChild(td);
                const type = "type" in column ? column.type : "string";
                if (column.source === "value" && field in string2value) {
                    td.innerHTML = string2value[field];
                } else if (column.source === "vervanger") {
                    const select = document.createElement("select")
                    td.appendChild(select);
                    select.dataset.type = "vervanger"
                    select.hidden = true;
                    if ("cb" in column && column.cb in string2cb) select.addEventListener("change", string2cb[column.cb]);
                } else {
                    const input = document.createElement("input");
                    td.appendChild(input);
                    input.dataset.field = field;
                    input.dataset.type = type;
                    input.value = item[field];
                    input.size = column.size;
                    if ("cb" in column && column.cb in string2cb) input.addEventListener("input", string2cb[column.cb]);
                }
            }
        }

        const __lesuur_changed = e => {
            const select = e.target.closest("tr").querySelector("[data-type=vervanger]");
            if (e.target.value in this.vervangers) {
                select.innerHTML = "";
                select.add(new Option("", "", true, true));
                this.vervangers[e.target.value].forEach(i => select.add(new Option(i, i)));
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

        const string2cb = {
            lesuur_changed: __lesuur_changed,
            vervanger_changed: __vervanger_changed
        }

        const string2value = {
            action_buttons
        }

        let table = null;
        if (add_to_table) {
            table = Info.info_table_tbl.querySelector("table");
        } else {
            Info.info_table_tbl.innerHTML = "";
            table = document.createElement("table");
            Info.info_table_tbl.appendChild(table);
            const tr = document.createElement("tr");
            table.appendChild(tr);
            for (const field of meta.school_info.fields) {
                const column = meta.field_info[field];
                const th = document.createElement("th");
                tr.appendChild(th);
                th.innerHTML = column.label;
            }
        }
        if (data.length > 0) { // use items from database
            for (const item of data) __draw_row(item)
        } else { // empty table
            const dummy_item = Object.fromEntries(meta.school_info.fields.map(i => [i, ""]));
            for (let i = 0; i < nbr_rows; i++) {
                dummy_item.id = this.id_ctr;
                this.id_ctr--;
                dummy_item.staff = current_user.username;
                __draw_row(dummy_item)
            }
        }
        // trigger the callbacks on columns/rows
        const rows = Array.from(table.querySelectorAll("tr"));
        rows.shift(); // drop header
        for (const row of rows) {
            for (const field of meta.school_info.fields) {
                const column = meta.field_info[field];
                if (column.source === "data" && "cb" in column) {
                    row.querySelector(`td [data-field=${field}]`).dispatchEvent(new Event("input"));
                }
            }
        }
        // attach an eventhandler on the "remove" button in each row
        Info.info_table_tbl.querySelectorAll(".btn-item-delete").forEach(r => r.addEventListener("click", e => {
            const tr = e.target.closest("tr");
            this.row_remove(tr)
        }));
        // attach an eventhandler on each input of the table so that, when at least on input is changed, the save button begins to blink
        Info.info_table_tbl.querySelectorAll("input").forEach(e => e.addEventListener("input", () => {
                this.info_save_btn.classList.add("blink-button");
                data = []
                const rows = Info.info_table_tbl.querySelectorAll('[data-id]');
                const date = document.getElementById("info-date").value;
                for (const row of rows) {
                    let item = {id: row.dataset.id};
                    const columns = row.querySelectorAll("[data-field]");
                    for (const column of columns) {
                        const field = column.dataset.field;
                        item[field] = column.value
                    }
                    if (item.lesuur > 0) data.push(item);
                }
                data.sort((a, b) => a.lesuur - b.lesuur);
                localStorage.setItem(`${global_data.school}-info-data`, JSON.stringify({info: data, date}));

            }
        ));
    }

    init_date_select = (view_date = null) => {
        const dagen = ["", "maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", ""];
        info_date_select.innerHTML = "";
        let date = new Date();
        for (let dag = 0; dag < 35; dag++) {
            let day_of_week = date.getDay() % 7;
            let date_label = date.toISOString().split("T")[0];
            if (dag === 0 && !view_date) view_date = date_label;
            if (dagen[day_of_week] !== "") {
                info_date_select.add(new Option(`${dag === 0 ? "Vandaag" : dagen[day_of_week]} (${date_label})`, date_label, view_date === date_label, view_date === date_label));
                if (day_of_week === 5) {
                    const option = new Option("-------------------------", null);
                    option.disabled = true;
                    info_date_select.add(option);
                }
            }
            date.setDate(date.getDate() + 1);
        }
        this.current_date = info_date_select.value;
        // when the date has changed, load en draw a new table
        info_date_select.addEventListener("change", async e => {
            e.preventDefault();
            e.stopImmediatePropagation();
            // cannot switch date when current table is not saved yet
            if (this.info_save_btn.classList.contains("blink-button")) {
                info_date_select.value = this.current_date;
                await bootbox.alert("Opgepast, je moet eerst bewaren vooraleer een andere datum te kiezen");
                return
            }
            //remove local (old) storage
            localStorage.removeItem(`${global_data.school}-info-data`);
            this.current_date = e.target.value;
            await this.load()
        });
    }

    load = async () => {
        // check if data is stored in local storage for current page (school).  If so, use this iso from database.
        this.local_storage = JSON.parse(localStorage.getItem(`${global_data.school}-info-data`));
        if (this.local_storage) {
            if (new Date(this.local_storage.date) >= new Date(new Date().setHours(0, 0, 0, 0))) {
                this.current_date = this.local_storage.date;
                info_date_select.value = this.current_date;
                // if the local storage is not empty, it means the data is not saved yet to the database
                this.info_save_btn.classList.add("blink-button");
            } else {
                this.local_storage = null;
            }
        }

        const resp_info = await fetch_get("infobord.infobord", {school: global_data.school, datum: this.current_date});
        if (resp_info) {
            resp_info.data.sort((a, b) => a.lesuur - b.lesuur);
            // prepare list of vervangers
            if ("vervangers" in resp_info && resp_info.vervangers.length > 0) {
                for (const v of resp_info.vervangers) {
                    if (v.lesuur in this.vervangers)
                        this.vervangers[v.lesuur].push(v.vervanger);
                    else
                        this.vervangers[v.lesuur] = [v.vervanger];
                }
            }
            // sort and remove double entries in the list of vervangers
            for (const [l, v] of Object.entries(this.vervangers)) this.vervangers[l] = [...new Set(v.sort())]

            if (this.local_storage)
                this.draw(this.local_storage.info);
            else
                this.draw(resp_info.data);
        }
        const resp_extra = await fetch_get("infobord.extrainfo", {school: global_data.school, datum: this.current_date});
        if (resp_extra.data) {
            this.extra_info.content_set(resp_extra.data.info);
            this.extra_info.id_set(resp_extra.data.id);
            this.extra_info.location_set(resp_extra.data.location + "-" + resp_extra.data.lesuur.toString());
        } else {
            this.extra_info.content_set("");
            this.extra_info.id_set(-1);
            this.extra_info.location_set("none-0");
        }
    }

    save = async () => {
        const rows = Info.info_table_tbl.querySelectorAll('[data-id]');
        const date = document.getElementById("info-date").value;
        let info_add = []
        let info_update = []
        for (const row of rows) {
            let item = {school: global_data.school, datum: `${date}`};
            const columns = row.querySelectorAll("[data-field]");
            for (const column of columns) {
                const field = column.dataset.field;
                if (column.dataset.type === "int" && column.value !== "") {
                    const value = parseInt(column.value);
                    if (isNaN(value)) {
                        bootbox.alert(`Opgepast, in kolom "${meta.field_info[column.dataset.field].label}" mag alleen een getal staan`)
                        return
                    }
                    item[field] = value;
                } else
                    item[field] = column.value
            }
            if (item.lesuur > 0)
                if (row.dataset.id <= -1) {
                    info_add.push(item);
                } else {
                    item.id = row.dataset.id;
                    info_update.push(item);
                }
        }
        if (info_add.length > 0) await fetch_post("infobord.infobord", info_add, {school: global_data.school, datum: info_date_select.value});
        if (info_update.length > 0) await fetch_update("infobord.infobord", info_update, {school: global_data.school, datum: info_date_select.value});
        if (this.info_delete.length > 0) await fetch_delete("infobord.infobord", {ids: this.info_delete.join(",")});
        const [location, lesuur] = this.extra_info.location_get().split("-");
        const extra_info_data = {lesuur: parseInt(lesuur), location, info: this.extra_info.content_get(), school: global_data.school, datum: `${date}`};
        if (this.extra_info.id_get() === "-1") {
            await fetch_post("infobord.extrainfo", extra_info_data, {school: global_data.school});
        } else {
            extra_info_data.id = this.extra_info.id_get();
            await fetch_update("infobord.extrainfo", extra_info_data, {school: global_data.school});
        }
        this.info_save_btn.classList.remove("blink-button");
        localStorage.removeItem(`${global_data.school}-info-data`);
        await this.load();
    }

    delete = async () => {
        bootbox.confirm({
            size: "small",
            message: "U gaat alle rijen wissen, zeker?",
            callback: async result => {
                if (result) {
                    const rows = Info.info_table_tbl.querySelectorAll('[data-id]');
                    for (const row of rows) this.row_remove(row);
                }
            }
        });
    }

    sort = async () => {
        const rows = Info.info_table_tbl.querySelectorAll('[data-id]');
        let data = []
        for (const row of rows) {
            let item = {school: global_data.school, id: row.dataset.id};
            const columns = row.querySelectorAll("[data-field]");
            for (const column of columns) {
                const field = column.dataset.field;
                if (column.dataset.type === "int") {
                    column.value = column.value === "" ? 0 : column.value;
                    const value = parseInt(column.value);
                    if (isNaN(value)) {
                        bootbox.alert(`Opgepast, in kolom "${meta.field_info[column.dataset.field].label}" mag alleen een getal staan`)
                        return
                    }
                    item[field] = value;
                } else
                    item[field] = column.value
            }
            if (item.lesuur > 0) data.push(item);
        }
        data.sort((a, b) => a.lesuur - b.lesuur); // sort on lesuur
        data.sort((a, b) => {
            if ((a.lesuur - b.lesuur) !== 0) return 0; // (sub)sort on klas
            return a.klas < b.klas ? -1 : 1
        })
        this.draw(data)
    }

    row_add = nbr => {
        this.draw([], nbr, true);
    }

    row_remove = row => {
        if (row.dataset.id !== "-1") this.info_delete.push(row.dataset.id);
        row.remove();
        this.info_save_btn.classList.add("blink-button");
    }

    column_index = name => {
        return meta.school_info.fields.indexOf(name);
    }

}

// Use arrow keys to navigate through the table.
const __init_arrow_keys = () => {
    document.addEventListener('keydown', (event) => {
        const current_td = document.activeElement.parentNode;
        const current_tr = current_td.parentNode;
        const index = Array.from(current_tr.children).indexOf(current_td);

        if (event.ctrlKey) {
            switch (event.key) {
                case "ArrowLeft":
                    // Left pressed
                    const input_left = current_td.previousElementSibling.getElementsByTagName('input')[0];
                    if (input_left) input_left.focus();
                    break;
                case "ArrowRight":
                    // Right pressed
                    const input_rigth = current_td.nextElementSibling.getElementsByTagName('input')[0];
                    if (input_rigth) input_rigth.focus();
                    break;
                case "ArrowUp":
                    // Up pressed
                    const input_up = Array.from(current_tr.previousElementSibling.children)[index].getElementsByTagName('input')[0];
                    if (input_up) input_up.focus();
                    break;
                case "ArrowDown":
                    // Down pressed
                    const row_down = current_tr.nextElementSibling;
                    if (row_down) {
                        const input_down = Array.from(row_down.children)[index].getElementsByTagName('input')[0];
                        if (input_down) input_down.focus();
                    }
                    break;
            }
        }
    })

}

// Type a staff code and press enter.  Relevant info (full name, schedule info) is fetched and fields in the row are populated.
let staff_cache = {};
const __init_shortcut = () => {
    staff_cache = Object.fromEntries(meta.staff.map(s => [s.code, s]))
    document.addEventListener('keyup', async event => {
        const current_td = document.activeElement.parentNode;
        const current_tr = current_td.parentNode;
        const index = Array.from(current_tr.children).indexOf(current_td);
        // consider the 3rd column only (Te vervangen)
        if (index === info.column_index("leerkracht")) {
            const value = document.activeElement.value;
            if (event.code === "Enter" && value.toUpperCase() in staff_cache) {
                const code = value.toUpperCase();
                const staff = staff_cache[code];
                document.activeElement.value = staff.roepnaam === "" ? `${staff.voornaam[0]}. ${staff.naam}` : staff.roepnaam;
                if (meta.school_info.use_schedule) {
                    const lesuur = current_tr.children[1].firstChild.value;
                    const day = new Date(document.getElementById("info-date").value).getDay();
                    const schedules = await fetch_get("infobord.schedule", {filters: `school$=$${global_data.school},dag$=$${day},lestijd$=$${lesuur},leerkracht$=$${code}`});
                    if (schedules.length > 0) {
                        let klascode = "";
                        let lokaal = [...new Set(schedules.map(s => s.lokaal))].join(", ");
                        if (global_data.school === "sum") klascode = schedules[0].klascode.substring(0, 2);
                        else if (global_data.school === "sui") klascode = [...new Set(schedules.map(s => s.klascode))].join(", ");
                        else if (global_data.school === "sul")
                            if (schedules.length === 1) {
                                klascode = schedules[0].klascode;
                            } else {
                                const klascodes = [...new Set(schedules.map(s => s.klascode))];
                                if (klascodes.length === 1)
                                    klascode = klascodes[0]
                                else
                                    klascode = [...new Set(klascodes.map(k => k.substring(0, 2)))].join(", ");
                            }
                        if (global_data.school === "sum")
                            current_tr.children[info.column_index("stamlokaal")].firstChild.value = lokaal;
                        else
                            current_tr.children[info.column_index("locatie")].firstChild.value = lokaal;
                        current_tr.children[info.column_index("klas")].firstChild.value = klascode;
                    }
                }
                current_tr.dataset["code"] = code
            }
        }
    });
}

const button_menu_items = [
    {
        type: 'button',
        id: 'info-save',
        label: 'Bewaar',
        cb: () => info.save()
    },
    {
        type: 'button',
        id: 'info-sort',
        label: 'Sorteer',
        cb: () => info.sort()
    },
    {
        type: 'button',
        id: 'info-delete',
        label: 'Leegmaken',
        cb: () => info.delete()
    },
    {
        type: 'button',
        id: 'info-add',
        label: '+5 rijen',
        cb: () => info.row_add(5)
    },
]

const __save_roepnaam = async (ids) => {
    const id = ids[0];
    const row = document.querySelector(`tr[data-id='${id}']`);
    const code = row.dataset.code;
    const roepnaam = row.children[2].firstChild.value;
    staff_cache[code].roepnaam = roepnaam;
    await fetch_update("infobord.staff", {id: staff_cache[code].id, roepnaam})
}

const __get_row_id = (event) => {
    return [event.target.parentNode.parentNode.dataset.id];
}

const context_menu_items = [
    {type: "item", label: 'Roepnaam bewaren', iconscout: 'plus-circle', cb: __save_roepnaam},
]

$(document).ready(async function () {
    if (current_user.level < 3)
        base_init({});
    else
        base_init({button_menu_items});

    info = new Info(document.getElementById("info-save"))
    info.init_date_select();
    await info.load();

    document.getElementById("preview").addEventListener("click", () => {
        window.open(window.location.origin + "/infobordview?school=" + global_data.school + "&datum=" + info_date_select.value + "&fontsize=x-large&preview=true", "_blank");
    });

    if (performance.getEntriesByType('navigation')[0].type === 'navigate') {
        console.log("voor de eerste keer bezocht")
    }
    __init_arrow_keys();
    __init_shortcut();

    const context_menu = new ContextMenu(document.getElementById("info-table"), context_menu_items);
    context_menu.subscribe_get_ids(__get_row_id);
});

