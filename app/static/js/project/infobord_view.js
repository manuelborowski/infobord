const table_meta = [
    {value: "lesuur", label: "Lesuur", source: "data", type: "int", size: 3},
    {value: "leerkracht", label: "Te vervangen", source: "data", size: 20},
    {value: "klas", label: "Klas", source: "data", size: 10},
    {value: "info", label: "Taak/Toets", source: "data", size: 15},
    {value: "locatie", label: "Lokaal", source: "data", size: 15},
    {value: "vervanger", label: "Vervanger", source: "data", size: 20},
]

const school2color = {
    sum: "#E3021D64",
    sul: "#525D267C",
    sui: "#034F9D91"
}

const __draw_table = (data) => {
    const info_table = document.getElementById("info-table");
    info_table.innerHTML = "";

    // const span = document.createElement("span");
    // info_table.appendChild(span);
    // span.style.display = "flex";
    // const h1 = document.createElement("h1");
    // span.appendChild(h1)
    // const now = new Date()
    // h1.innerHTML = now.toLocaleDateString('nl-NL', {weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',});
    // const img = document.createElement("img");
    // span.appendChild(img);
    // img.src = `/static/img/${global_data.school}.png`
    // img.style.width = "75px";
    // img.style.height = "75px";

    if (data.length === 0) {
        info_table.innerHTML = "Tabel is leeg";
        return
    }
    data.sort((a, b) => a.lesuur - b.lesuur);
    const table = document.createElement("table");
    info_table.appendChild(table);
    const tr = document.createElement("tr");
    table.appendChild(tr);
    for (const column of table_meta) {
        const th = document.createElement("th");
        tr.appendChild(th);
        th.innerHTML = column.label;
    }
    const now = new Date();
    const now_reference = now.getHours() * 100 + now.getMinutes();

    let view_minimum_lesuur = 9;
    for (let i=9; i > 0; i--) {
        let [h, m] = global_data.lestijden[i].split(".").map(i => parseInt(i));
        if ((h * 100 + m) < now_reference) {
            view_minimum_lesuur = i;
            break;
        }
    }

    let lesuur = "";
    for (const item of data) {
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
}

$(document).ready(function () {
    if (global_data.font_size) document.querySelector("body").style.fontSize = global_data.font_size;
    __draw_table(global_data.info);
});

