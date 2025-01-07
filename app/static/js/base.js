import {ButtonMenu} from "./common/button_menu.js";

var menu = [
    ["incident.show", "Incidenten", 1],
    ["history.show", "Historiek", 1],
    ["spare.show", "Reserves", 3],
    ["lisbadge.show", "LIS badges", 3],
    ["user.show", "Gebruikers", 5],
    ["settings.show", "Instellingen", 5],
]

export const inject_menu = new_menu => {
    menu = new_menu;
}

export const base_init = ({button_menu_items=[]}) => {
    if (suppress_navbar) return;

    if (default_view) { // after login, go to default (= first) page
        document.location.href = Flask.url_for(menu[0][0])
    }
    const navbar_element = document.querySelector("#navbar");
    let dd_ctr = 0;
    for (const item of menu) {
        if (current_user.level >= item[2]) {
            const li = document.createElement("li");
            if (Array.isArray(item[0])) {
                // dropdown menu-item
                li.classList.add("nav-item", "dropdown");
                const a = document.createElement("a");
                li.appendChild(a)
                a.classList.add("nav-link", "dropdown-toggle");
                a.href = "#";
                a.id = `dd${dd_ctr}`
                a.setAttribute("role", "button");
                a.setAttribute("data-toggle", "dropdown");
                a.setAttribute("aria-haspopup", true);
                a.setAttribute("aria-expanded", true);
                a.innerHTML = item[1];
                const div = document.createElement("div");
                li.appendChild(div)
                div.classList.add("dropdown-menu");
                div.setAttribute("aria-labelledby", `dd${dd_ctr}`)
                for (const sitem of item[0]) {
                    if (sitem[0] === "divider") {
                        const divd = document.createElement("div");
                        divd.classList.add("dropdown-divider");
                        div.appendChild(divd)
                    } else {
                        if (current_user.level >= sitem[2]) {
                            const a = document.createElement("a");
                            div.appendChild(a)
                            a.classList.add("dropdown-item");
                            if (typeof sitem[0] === "function") {
                                a.onclick = sitem[0];
                            } else {
                                a.href = Flask.url_for(sitem[0]);
                            }
                            a.innerHTML = sitem[1]
                        }
                    }
                }
                dd_ctr++;
            } else {
                // regular menu-item
                const url_path = Flask.url_for(item[0]);
                li.classList.add("nav-item");
                const a = document.createElement("a");
                a.classList.add("nav-link");
                if (window.location.href.includes(url_path)) {
                    a.classList.add("active");
                }
                a.href = url_path;
                a.innerHTML = item[1];
                li.appendChild(a);
            }
            navbar_element.appendChild(li);
        }
    }

    if (stand_alone) {
        const btn_div = document.createElement("div");
        btn_div.classList.add("nav-buttons");
        const sync_btn = document.createElement("button");
        sync_btn.classList.add("btn", "btn-warning");
        sync_btn.type = "button";
        sync_btn.onclick = start_sync;
        sync_btn.innerHTML = "Sync";
        btn_div.appendChild(sync_btn);
        navbar_element.appendChild(btn_div);

        // const upgrade_div = document.createElement("div");
        // upgrade_div.classList.add("nav-buttons");
        // const upgade_btn = document.createElement("button");
        // upgade_btn.classList.add("btn", "btn-warning");
        // upgade_btn.type = "button";
        // upgade_btn.onclick = start_upgrade;
        // upgade_btn.innerHTML = "Upgrade";
        // upgrade_div.appendChild(upgade_btn);
        // navbar_element.appendChild(upgrade_div);
    }

    const button_menu = new ButtonMenu(document.querySelector(".button-menu-placeholder"), button_menu_items);
}

