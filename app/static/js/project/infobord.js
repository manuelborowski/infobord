import {base_init} from "../base.js";
import {fetch_delete, fetch_get, fetch_post, fetch_update} from "../common/common.js";
import {ContextMenu} from "../common/context_menu.js";

let meta = await fetch_get("infobord.meta", {school: global_data.school});
const code2staff = Object.fromEntries(meta.staff.map(s => [s.code, s]))
let info = null;
const info_date_select = document.getElementById("info-date");

const format_sul_klascode = schedules => {
    const grouped_klassen = {};
    for (const schedule of schedules) {
        // klasgroep: 4A, klas: GL4
        const [klasgroep, klas] = schedule.klascode.split(" ", 2);
        if (!klasgroep || !klas) continue;
        if (!(klasgroep in grouped_klassen)) grouped_klassen[klasgroep] = [];
        if (!grouped_klassen[klasgroep].includes(klas)) grouped_klassen[klasgroep].push(klas);
    }
    return Object.entries(grouped_klassen).map(([klasgroep, klassen]) => {
        const all_klassen = meta.klasgroepen?.[klasgroep] ?? [];
        // A complete klasgroep is returned as just the klasgroep.
        if (all_klassen.length > 0 && klassen.length === all_klassen.length) return klasgroep;
        // return the klasgroep, together with a list of klassen
        return klassen.sort().map(klas => `${klasgroep} ${klas}`).join(", ");
    }).join(", ");
}

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
    static message_type_labels = {
        "geen": "Geen",
        "at-home": "Thuis",
        "to-home": "Naar Huis",
    }

    static normalize_bericht = value => {
        if (value === true || value === "true") return "at-home";
        if (value === false || value === "false" || value === null || value === "") return "geen";
        return value in Info.message_type_labels ? value : "geen";
    }

    static split_klassen = klas => (klas || "").split(",").map(k => k.trim()).filter(k => k !== "");

    static append_list = (parent, items) => {
        const ul = document.createElement("ul");
        parent.appendChild(ul);
        if (items.length === 0) {
            const li = document.createElement("li");
            li.textContent = "-";
            ul.appendChild(li);
        }
        for (const item of items) {
            const li = document.createElement("li");
            li.textContent = item;
            ul.appendChild(li);
        }
    }

    // clean up value: remove unnecessary spaces. convert to uppercase and make sure it is a string
    static text_key = value => String(value || "").trim().replace(/\s+/g, " ").toUpperCase();

    static staff_display_name = staff => {
        if (staff.roepnaam && staff.roepnaam.trim()) return staff.roepnaam.trim();
        if (staff.voornaam && staff.naam) return `${staff.voornaam[0]}. ${staff.naam}`;
        return staff.naam || staff.voornaam || staff.code;
    }

    // find a staff-object from the code, and convert it to a proper label (V. Naam)
    static staff_name = code => {
        const receiver_code = String(code || "").trim().toUpperCase();
        const staff = code2staff[receiver_code];
        if (!staff) return code;
        return Info.staff_display_name(staff);
    }

    // build a clean list of possible combinations of staff naam, voornaam and roepnaam
    static staff_match_values = staff => [
        staff.code,
        staff.naam,
        staff.voornaam,
        staff.roepnaam,
        [staff.voornaam, staff.naam].filter(Boolean).join(" "),
        staff.voornaam && staff.naam ? `${staff.voornaam[0]}. ${staff.naam}` : "",
    ].map(Info.text_key).filter(Boolean);

    // Trye to match L. Franiuc to FRAL
    static staff_from_text = value => {
        const key = Info.text_key(value);
        if (!key) return null;
        // try to find a single match of the key (L. FRANIIUC) in a list of possible matches (FRAL, FRANIUC, L. FRANIUC, ...)
        const matches = (meta.staff || []).filter(staff => Info.staff_match_values(staff).includes(key));
        // matches[0] always contains the code (FRAL)
        return matches.length === 1 ? matches[0] : null;
    }

    // create a list of unique {staff-code, ticked} objects
    static receiver_options = ({settings_receivers, leerkracht, vervanger}) => {
        const receivers = new Map();
        const add_receiver = (code, checked) => {
            const receiver_code = String(code || "").trim().toUpperCase();
            if (!receiver_code) return;
            if (!receivers.has(receiver_code)) receivers.set(receiver_code, {code: receiver_code, checked});
            else receivers.get(receiver_code).checked = receivers.get(receiver_code).checked || checked;
        }
        // Add the receivers from settings, these are default ticked
        for (const code of settings_receivers || []) add_receiver(code, true);
        // Add the replaced staff and replacement staff by matching the content of the column to a staff.  These are default unticked
        for (const value of [leerkracht, vervanger]) {
            const staff = Info.staff_from_text(value);
            if (staff) add_receiver(staff.code, false);
        }
        return [...receivers.values()];
    }

    // HTML specific, create the list of additional receivers
    static append_receiver_checkboxes = (parent, receivers) => {
        const ul = document.createElement("ul");
        parent.appendChild(ul);
        if (receivers.length === 0) {
            const li = document.createElement("li");
            li.textContent = "-";
            ul.appendChild(li);
            return [];
        }
        const inputs = [];
        for (const receiver of receivers) {
            const li = document.createElement("li");
            ul.appendChild(li);
            const label = document.createElement("label");
            li.appendChild(label);
            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.checked = receiver.checked;
            checkbox.dataset.code = receiver.code;
            checkbox.style.marginRight = "0.4rem";
            label.appendChild(checkbox);
            label.appendChild(document.createTextNode(Info.staff_name(receiver.code)));
            inputs.push(checkbox);
        }
        return inputs;
    }

    static prompt_smartschool_message = ({message_type, klas, leerkracht, vervanger}) => {
        const settings = meta.smartschool_message || {};
        const template = settings.templates?.[message_type] || {title: "", body: ""};
        const popup = document.createElement("div");
        popup.classList.add("smartschool-message-compose");
        const receivers = Info.receiver_options({settings_receivers: settings.additional_receivers || [], leerkracht, vervanger});

        const klas_section = document.createElement("section");
        popup.appendChild(klas_section);
        const klas_title = document.createElement("h5");
        klas_title.textContent = "Klassen";
        klas_section.appendChild(klas_title);
        Info.append_list(klas_section, Info.split_klassen(klas));

        const receivers_section = document.createElement("section");
        popup.appendChild(receivers_section);
        const receivers_title = document.createElement("h5");
        receivers_title.textContent = "Extra ontvangers";
        receivers_section.appendChild(receivers_title);
        const receiver_inputs = Info.append_receiver_checkboxes(receivers_section, receivers);

        const title_label = document.createElement("label");
        title_label.textContent = "Onderwerp";
        popup.appendChild(title_label);
        const title_input = document.createElement("input");
        title_input.classList.add("form-control");
        title_input.value = template.title || "";
        popup.appendChild(title_input);

        const body_label = document.createElement("label");
        body_label.textContent = "Bericht";
        popup.appendChild(body_label);
        const body_editor = document.createElement("div");
        body_editor.classList.add("smartschool-message-body-editor");
        popup.appendChild(body_editor);

        const variables = document.createElement("p");
        variables.classList.add("smartschool-message-variables");
        variables.textContent = `Mogelijke variabelen: ${(settings.variables || []).join(", ")}`;
        popup.appendChild(variables);
        const template_tags = document.createElement("p");
        template_tags.classList.add("smartschool-message-variables");
        template_tags.textContent = `Mogelijke tags: ${(settings.template_tags || []).join(", ")}`;
        popup.appendChild(template_tags);

        return new Promise(resolve => {
            let quill = null;
            const initialise_body_editor = () => {
                if (quill) return;
                quill = new Quill(body_editor, {theme: "snow"});
                quill.clipboard.dangerouslyPasteHTML(template.body || "");
            }
            const dialog = bootbox.dialog({
                title: `Smartschool bericht: ${Info.message_type_labels[message_type]}`,
                message: popup,
                size: "xl",
                className: "smartschool-message-dialog",
                buttons: {
                    cancel: {
                        label: "Annuleer",
                        className: "btn-secondary",
                        callback: () => resolve(null)
                    },
                    send: {
                        label: "Verzenden",
                        className: "btn-success",
                        callback: () => resolve({
                            title: title_input.value,
                            body: quill ? quill.root.innerHTML : template.body || "",
                            additional_receivers: receiver_inputs.filter(input => input.checked).map(input => input.dataset.code),
                        })
                    }
                }
            });
            dialog.on("shown.bs.modal", initialise_body_editor);
            setTimeout(initialise_body_editor, 0);
        });
    }

    constructor(info_save_btn) {
        this.info_save_btn = info_save_btn;
        this.info_delete = [];
        this.extra_info = new ExtraInfo(info_save_btn);
        this.id_ctr = -1;
    }

    field_value = (column) => {
        if (column.type === "checkbox") return column.checked;
        return column.value;
    }

    draw = (data = [], nbr_rows = 20, add_to_table = false) => {
        const action_buttons = ` <a type="button" class="btn-item-delete btn btn-success"><i class="fa-solid fa-xmark" title="Lijn verwijderen"></i></a></div> `

        const __color_cell = (cell, color) => {
            cell.style.background = color;
            cell.children[0].style.background = color;
        }

        const __recent_update_color_row = (row, recent_update) => {
            if (meta.school_info.mark_recent_update) {
                if (recent_update) {
                    if (meta.school_info.mark_recent_update.type === "color")
                        row.style.backgroundColor = meta.school_info.mark_recent_update.value;
                } else {
                    row.style.backgroundColor = "";
                }
            }
        }

        const __draw_row = (item) => {
            const tr = document.createElement("tr");
            __recent_update_color_row(tr, item.recent_update);
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
                    // Add empty option
                    select.add(new Option("\xA0\xA0\xA0\xA0\xA0\xA0\xA0\xA0", "null"))
                    // A click will use lesuur, date and school to fetch the standby staff from the server and populate the select
                    select.addEventListener("click", e => __vervanger_clicked(e));
                    // A change will copy the value from the select to the column "vervanger"
                    select.addEventListener("change", e => __vervanger_changed(e));
                } else if (column.source === "bericht" && item.id > 0) { // consider valid entries only
                    const select = document.createElement("select")
                    td.appendChild(select);
                    select.dataset.field = "bericht";
                    item[field] = Info.normalize_bericht(item[field]);
                    tr.dataset.berichtValue = item[field];
                    Object.entries(Info.message_type_labels).forEach(([value, label]) => {select.add(new Option(label, value, value === item[field], value === item[field]))});
                    __color_cell(td, item[field] !== "geen" ? "yellow" : "");
                    if ("cb" in column && column.cb in string2cb) select.addEventListener("change", string2cb[column.cb]);
                } else if (column.source === "recent_update" && item.id > 0) { // consider valid entries only
                    const div = document.createElement("div");
                    td.appendChild(div);
                    div.classList.add("form-check", "form-switch");
                    const input = document.createElement("input");
                    div.appendChild(input);
                    input.classList.add("form-check-input");
                    input.dataset.field = "recent_update";
                    input.type = "checkbox";
                    input.checked = item[field];
                    input.style.marginLeft = "0.5em";
                    if ("cb" in column && column.cb in string2cb) input.addEventListener("click", string2cb[column.cb]);
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

        const __vervanger_clicked = async e => {
            // this is called twice, first to populate and open the select, then when a selection is made.  Ignore the second click
            if (e.target.options.length > 1) return
            const day = new Date(document.getElementById("info-date").value).getDay();
            const current_tr = e.target.closest("tr");
            const lesuur = current_tr.children[1].firstChild.value;
            for (const standby_code of meta.school_info.standby_code) {
                const schedules = await fetch_get("infobord.schedule", {filters: `school$=$${global_data.school},dag$=$${day},lestijd$=$${lesuur},vak$=$${standby_code}`});
                for (const schedule of schedules) {
                    const staff = code2staff[schedule.leerkracht];
                    const name = staff.roepnaam === "" ? `${staff.voornaam[0]}. ${staff.naam}` : staff.roepnaam;
                    e.target.add(new Option(`(${standby_code}) ${name}`, name));
                }
            }
            // Add, if required, the default standby options
            if (meta.school_info.default_standby) {
                meta.school_info.default_standby.forEach(i => e.target.add(new Option(i, i)));
            }
        }

        const __vervanger_changed = e => {
            const value = e.target.value;
            if (value === "null") return
            const vervanger_field = e.target.closest("tr").querySelector("[data-field=vervanger]");
            vervanger_field.value = value;
            this.info_save_btn.classList.add("blink-button");
        }

        // create a popup for additional information or adaptations and send to backend.
        const __message_send = async e => {
            const value = Info.normalize_bericht(e.target.value);
            const row = e.target.closest("tr");
            const message_sent = row.querySelector("[data-field=bericht]");
            const previous_value = Info.normalize_bericht(row.dataset.berichtValue);
            if (value === previous_value) return;

            let data = {id: row.dataset.id, bericht: value};
            row.querySelectorAll("[data-field]").forEach(column => {
                const field = column.dataset.field;
                if (field === "bericht") {
                    data[field] = value;
                } else if (column.dataset.type === "int") {
                    data[field] = parseInt(column.value);
                } else {
                    data[field] = this.field_value(column);
                }
            });
            if (value !== "geen") {
                const popup_data = await Info.prompt_smartschool_message({
                    message_type: value,
                    klas: data.klas || "",
                    leerkracht: data.leerkracht || "",
                    vervanger: data.vervanger || "",
                });
                if (!popup_data) {
                    message_sent.value = previous_value;
                    return;
                }
                data = {...data, message_title: popup_data.title, message_body: popup_data.body, message_additional_receivers: popup_data.additional_receivers};
            }

            const response = await fetch_update("infobord.infobord", [data]);
            if (response === null) {
                await this.load();
                return;
            }
            row.dataset.berichtValue = value;
            __color_cell(e.target.closest("td"), value !== "geen" ? "yellow" : "");
        }

        const __recent_update_changed = async e => {
            const value = e.target.value;
            const row = e.target.closest("tr");
            const recent_update = row.querySelector("[data-field=recent_update]");
            await fetch_update("infobord.infobord", [{id: row.dataset.id, recent_update: recent_update.checked}]);
            __recent_update_color_row(row, recent_update.checked);
        }

        const string2cb = {
            vervanger_changed: __vervanger_changed,
            message_sent: __message_send,
            recent_update: __recent_update_changed,
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
        Info.info_table_tbl.querySelectorAll("input").forEach(e => e.addEventListener("input", (e) => {
                if (meta.field_info[e.target.dataset.field].localstorage === false) return // no localstorage required
                this.info_save_btn.classList.add("blink-button");
                data = []
                const rows = Info.info_table_tbl.querySelectorAll('[data-id]');
                const date = document.getElementById("info-date").value;
                for (const row of rows) {
                    let item = {id: row.dataset.id};
                    const columns = row.querySelectorAll("[data-field]");
                    for (const column of columns) {
                        const field = column.dataset.field;
                        item[field] = this.field_value(column);
                    }
                    if (item.lesuur > 0) data.push(item);
                }
                data.sort((a, b) => a.lesuur - b.lesuur);
                localStorage.setItem(`${global_data.school}-info-data`, JSON.stringify({info: data, date}));

            }
        ));
    }

    init_date_select = (view_date = null) => {
        info_date_select.innerHTML = "";
        let date = new Date();
        const dagen = date.getDay() > 0 && date.getDay() < 6 ? ["", "maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", ""] : ["zondag", "maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag"];
        date.setDate(date.getDate() - 15);
        for (let dag = -15; dag < 35; dag++) {
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
            if (dag === 0) info_date_select.querySelector(`option[value="${date_label}"`).style.background = "yellow";
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
            // Only local storage of today is valid.
            if (new Date(this.local_storage.date) >= new Date(new Date().setHours(0, 0, 0, 0))) {
                this.current_date = this.local_storage.date;
                info_date_select.value = this.current_date;
                // if the local storage is not empty, it means the data is not saved yet to the database
                this.info_save_btn.classList.add("blink-button");
                // convert string "true", "on" to boolean true and "false", "off" to false
                this.local_storage.info = this.local_storage.info.map(r => Object.fromEntries(Object.entries(r).map((([k, v]) => {
                    return [k, ["true", "on"].includes(v) ? true : ["false", "off"].includes(v) ? false : v]
                }))));
            } else {
                this.local_storage = null;
            }
        }

        const resp_info = await fetch_get("infobord.infobord", {school: global_data.school, datum: this.current_date});
        if (resp_info) {
            resp_info.data.sort((a, b) => a.lesuur - b.lesuur);
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
            let item = {};
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
                    item[field] = this.field_value(column)
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
        if (info_update.length > 0) {
            const response = await fetch_update("infobord.infobord", info_update);
            if (response === null) return;
        }
        if (this.info_delete.length > 0) await fetch_delete("infobord.infobord", {ids: this.info_delete.join(",")});
        const [location, lesuur] = this.extra_info.location_get().split("-");
        const extra_info_data = {lesuur: parseInt(lesuur), location, info: this.extra_info.content_get()};
        if (this.extra_info.id_get() === "-1") {
            await fetch_post("infobord.extrainfo", extra_info_data, {school: global_data.school, datum: date});
        } else {
            extra_info_data.id = this.extra_info.id_get();
            await fetch_update("infobord.extrainfo", extra_info_data);
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
            let item = {id: row.dataset.id};
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
                    item[field] = this.field_value(column)
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
const __init_shortcut = () => {
    document.addEventListener('keyup', async event => {
        const current_td = document.activeElement.parentNode;
        const current_tr = current_td.parentNode;
        const index = Array.from(current_tr.children).indexOf(current_td);
        // consider the 3rd column only (Te vervangen)
        if (index === info.column_index("leerkracht")) {
            const value = document.activeElement.value;
            if (event.code === "Enter" && value.toUpperCase() in code2staff) {
                const code = value.toUpperCase();
                const staff = code2staff[code];
                document.activeElement.value = staff.roepnaam === "" ? `${staff.voornaam[0]}. ${staff.naam}` : staff.roepnaam;
                if (meta.school_info.use_schedule) {
                    const lesuur = current_tr.children[1].firstChild.value;
                    const day = new Date(document.getElementById("info-date").value).getDay();
                    // Try to fill the klascode and lokaal fields
                    let schedules = await fetch_get("infobord.schedule", {filters: `school$=$${global_data.school},dag$=$${day},lestijd$=$${lesuur},leerkracht$=$${code}`});
                    if (schedules.length > 0) {
                        let klascode = "";
                        let lokaal = [...new Set(schedules.map(s => s.lokaal))].join(", ");
                        if (global_data.school === "sum") klascode = schedules[0].klascode.substring(0, 2);
                        else if (global_data.school === "sui") klascode = [...new Set(schedules.map(s => s.klascode))].join(", ");
                        else if (global_data.school === "sul") klascode = format_sul_klascode(schedules);
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
    code2staff[code].roepnaam = roepnaam;
    await fetch_update("infobord.staff", {id: code2staff[code].id, roepnaam})
}

const __row_to_item = (row) => {
    const item = {};
    for (const field of meta.school_info.fields) {
        const column = row.querySelector(`[data-field=${field}]`);
        if (!column) continue;
        if (column.dataset.type === "int") {
            const value = parseInt(column.value);
            item[field] = isNaN(value) ? 0 : value;
        } else if (column.type === "checkbox") {
            item[field] = column.checked;
        } else {
            item[field] = column.value;
        }
    }
    return item;
}

const __row_to_copied_item = (row) => {
    const item = __row_to_item(row);
    item.bericht = "geen";
    item.recent_update = false;
    item.remark = "";
    return item;
}

const __prompt_copy_until_date = () => {
    return new Promise(resolve => {
        bootbox.prompt({
            title: "Kopieer deze lijn tot en met",
            inputType: "date",
            value: info_date_select.value,
            callback: result => resolve(result),
        });
    });
}

const __parse_date = value => {
    const [year, month, day] = value.split("-").map(Number);
    return new Date(year, month - 1, day);
}

const __format_date = date => {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, "0");
    const day = date.getDate().toString().padStart(2, "0");
    return `${year}-${month}-${day}`;
}

// Copy the select line, each time one week later, until the selected date.
const __copy_row_weekly = async (ids) => {
    const id = ids[0];
    const row = document.querySelector(`tr[data-id='${id}']`);
    if (!row) return;

    const source_date = __parse_date(info_date_select.value);
    const end_date_value = await __prompt_copy_until_date();
    if (!end_date_value) return;

    const end_date = __parse_date(end_date_value);
    const source_timestamp = Date.UTC(source_date.getFullYear(), source_date.getMonth(), source_date.getDate());
    const end_timestamp = Date.UTC(end_date.getFullYear(), end_date.getMonth(), end_date.getDate());
    const days_between = Math.round((end_timestamp - source_timestamp) / (24 * 60 * 60 * 1000));
    if (days_between <= 0 || days_between % 7 !== 0) {
        bootbox.alert("Kies een datum minstens 1 week later op dezelfde weekdag.");
        return;
    }
    let copy_count = 0;
    const copy_date = new Date(source_date);
    copy_date.setDate(copy_date.getDate() + 7);
    while (copy_date <= end_date) {
        const datum = __format_date(copy_date);
        await fetch_post("infobord.infobord", [__row_to_copied_item(row)], {school: global_data.school, datum});
        copy_count++;
        copy_date.setDate(copy_date.getDate() + 7);
    }
    bootbox.alert(`${copy_count} lijn(en) gekopieerd.`);
}

const __get_row_id = (event) => {
    return [event.target.closest("tr").dataset.id];
}

const context_menu_items = [
    {type: "item", label: 'Roepnaam bewaren', iconscout: 'plus-circle', cb: __save_roepnaam},
    {type: "item", label: 'Kopieer deze lijn', iconscout: 'copy', cb: __copy_row_weekly},
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
