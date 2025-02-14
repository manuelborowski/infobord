const table_meta = [
    {value: "lesuur", label: "Lesuur", source: "data", type: "int", size: 3},
    {value: "leerkracht", label: "Te vervangen", source: "data", size: 20},
    {value: "klas", label: "Klas", source: "data", size: 10},
    {value: "info", label: "Taak/Toets", source: "data", size: 15},
    {value: "locatie", label: "Lokaal", source: "data", size: 15},
    {value: "vervanger", label: "Vervanger", source: "data", size: 20},
]

const table = document.createElement("table");

const school2color = {
    sum: "rgb(237 85 104 / 39%)",
    sul: "rgb(216 227 170 / 49%)",
    sui: "rgb(119 169 221 / 57%)"
}

const __draw_table = () => {

    let __info_injected = false;
    const __inject_extra_info = () => {
        if (global_data.extra_info && global_data.extra_info.location === "lesuur") {
            const tr = document.createElement("tr");
            table.appendChild(tr);
            const td = document.createElement("td");
            tr.appendChild(td);
            td.colSpan = 6;
            td.style.textAlign = "center";
            td.innerHTML = global_data.extra_info.info;
            __info_injected = true;
        } else if (global_data.extra_info && global_data.extra_info.location === "left") {
            document.getElementById("view-extra-info").innerHTML = global_data.extra_info.info;
        }
    }

    const view_table = document.getElementById("view-table");
    const view_date = document.getElementById("view-date");
    view_table.innerHTML = "";
    if (global_data.info.length === 0) {
        view_table.innerHTML = "Tabel is leeg";
        return
    }
    global_data.info.sort((a, b) => a.lesuur - b.lesuur);
    view_table.appendChild(table);
    const tr = document.createElement("tr");
    table.appendChild(tr);
    for (const column of table_meta) {
        const th = document.createElement("th");
        tr.appendChild(th);
        th.innerHTML = column.label;
    }
    const now = new Date();
    const now_reference = now.getHours() * 100 + now.getMinutes();

    let view_minimum_lesuur = 1;
    if (global_data.preview) {
        view_date.innerHTML = global_data.date;
    } else {
        for (let i = 9; i > 0; i--) {
            let [h, m] = global_data.lestijden[i].split(".").map(i => parseInt(i));
            if ((h * 100 + m) < now_reference) {
                view_minimum_lesuur = i;
                break;
            }
        }
    }
    let lesuur = "";
    for (const item of global_data.info) {
        if (global_data.extra_info && global_data.extra_info.location === "lesuur" && global_data.extra_info.lesuur <= item.lesuur && !__info_injected) __inject_extra_info()
        if (item.lesuur < view_minimum_lesuur) continue;
        item.lesuur = `${item.lesuur}: ${global_data.lestijden[item.lesuur]}`
        if (item.lesuur !== lesuur)
            lesuur = item.lesuur;
        else
            item.lesuur = "";
        const tr = document.createElement("tr");
        table.appendChild(tr);
        for (const column of table_meta) {
            const td = document.createElement("td");
            tr.appendChild(td);
            td.innerHTML = item[column.value];
            if (item.lesuur === "") td.style.borderTopStyle = "none";
        }
    }
    table.style.background = school2color[global_data.school];
    table.style.widows = "1200px";
    if (global_data.extra_info && global_data.extra_info.location === "left") __inject_extra_info();
}

$(document).ready(function () {
    if (global_data.font_size) document.querySelector("body").style.fontSize = global_data.font_size;
    if (global_data.width) table.style.width = global_data.width;
    __draw_table();
});

