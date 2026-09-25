/* ========================================================
   Rugby LNR Game Card — v0.1.0
   Carte Lovelace pour les sensors de l'intégration rugby_lnr
   (TOP 14 / PRO D2 — https://github.com/developpeurbox/hass-rugby-lnr)
   ======================================================== */

const RUGBY_LNR_GAME_CARD_VERSION = "v0.0.1";

class RugbyLnrGameCard extends HTMLElement {

  constructor() {
    super();
    this._uid = "rugbylnr-" + Math.random().toString(36).slice(2, 9);
  }

  setConfig(config) {
    if (!config.entity) throw new Error("Vous devez définir une entité.");
    this._config = config;
    console.info(`%c RUGBY-LNR-GAME-CARD %c ${RUGBY_LNR_GAME_CARD_VERSION} `, "color:#e63946;background:#1e1e2e;font-weight:700;padding:2px 4px;border-radius:4px 0 0 4px", "color:#1e1e2e;background:#e63946;font-weight:700;padding:2px 4px;border-radius:0 4px 4px 0");
    if (this._hass) this.hass = this._hass;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._config) return;

    const state = hass.states[this._config.entity];
    if (!state) {
      this.innerHTML = `<ha-card style="padding:16px;color:red">Entité introuvable : ${this._config.entity}</ha-card>`;
      return;
    }

    const b   = state.attributes;
    const uid = this._uid;

    const now = new Date();
    const fin = b.datetime_fin ? new Date(b.datetime_fin.replace(" ", "T")) : null;

    this.style.setProperty("--rugby-footer-bg",    this._config.footer_bg    || "rgba(0,0,0,0.45)");
    this.style.setProperty("--rugby-footer-color", this._config.footer_color || "#e63946");

    const pasDeMatch = (fin && fin < now) || (!b.domicile && !b.exterieur);

    if (pasDeMatch) {
      const logoTeam = b.logoTeam || "";
      const teamName = b.team || "";

      this.innerHTML = `
        <ha-card>
          <style>
            #${uid} .rug-card {
              background: #1e1e2e;
              border-radius: 16px;
              position: relative;
              overflow: hidden;
              border: 1px solid rgba(255,255,255,.07);
              font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            }
            #${uid} .rug-top { position: relative; padding: 18px 16px 14px; }
            #${uid} .rug-body { position: relative; z-index: 1; }
            #${uid} .rug-empty {
              display: flex; flex-direction: column; align-items: center; gap: 10px;
            }
            #${uid} .team-logo-wrap {
              position: relative; width: 72px; height: 72px;
              display: flex; align-items: center; justify-content: center;
            }
            #${uid} .team-logo-ghost {
              position: absolute; top: 50%; left: 50%;
              width: 170px; height: 170px; transform: translate(-50%, -50%);
              object-fit: contain; opacity: .15;
              filter: grayscale(40%) blur(1px); pointer-events: none; z-index: 0;
            }
            #${uid} .team-logo {
              position: relative; z-index: 1; width: 72px; height: 72px;
              object-fit: contain; filter: drop-shadow(0 4px 14px rgba(0,0,0,.7));
            }
            #${uid} .team-name {
              font-size: 13px; font-weight: 600; color: rgba(255,255,255,.75); text-align: center;
            }
            #${uid} .no-match-msg {
              font-size: 11px; color: rgba(255,255,255,.35); text-align: center; font-style: italic;
            }
          </style>
          <div id="${uid}">
            <div class="rug-card">
              <div class="rug-top">
                <div class="rug-body">
                  <div class="rug-empty">
                    <div class="team-logo-wrap">
                      ${logoTeam ? `<img class="team-logo-ghost" src="${logoTeam}">` : ""}
                      ${logoTeam
                        ? `<img class="team-logo" src="${logoTeam}">`
                        : `<div style="width:72px;height:72px"></div>`}
                    </div>
                    ${teamName ? `<span class="team-name">${teamName}</span>` : ""}
                    <span class="no-match-msg">Aucun match prévu prochainement</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </ha-card>
      `;
      return;
    }

    const logoDom     = b.logoDomicile  || "";
    const logoExt     = b.logoExterieur || "";
    const gameName    = b.game          || "";
    const competition = [b.competition, b.journee].filter(Boolean).join(" · ");
    const diffuseur1 = b.diffuseur1 || "";
    const logoDiff1 = b.logoDiffuseur1 || "";
    const diffuseur2 = b.diffuseur2 || "";
    const logoDiff2 = b.logoDiffuseur2 || "";
    const heure       = b.heure         || "";
    const date        = b.date_fr || b.date || "";

    this.innerHTML = `
      <ha-card>
        <style>
          #${uid} .rug-card {
            background: #1e1e2e;
            border-radius: 16px;
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,.07);
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
          }
          #${uid} .rug-top { position: relative; padding: 18px 16px 14px; }
          #${uid} .rug-body { position: relative; z-index: 1; }
          #${uid} .rug-game { text-align: center; margin-bottom: 20px; }
          #${uid} .rug-game-name {
            font-weight: 700; color: #e0e0f0; font-size: 16px; display: block;
          }
          #${uid} .rug-game-competition {
            font-size: 12px; color: rgba(255,255,255,.4); display: block;
            margin-top: 3px; font-style: italic;
          }
          #${uid} .teams {
            display: flex; justify-content: center; align-items: center;
            gap: clamp(20px, 8%, 64px);
          }
          #${uid} .team-block {
            display: flex; flex-direction: column; align-items: center;
            gap: 6px; width: 80px; flex: 0 0 auto;
          }
          #${uid} .team-logo-wrap {
            position: relative; width: 72px; height: 72px;
            display: flex; align-items: center; justify-content: center;
          }
          #${uid} .team-logo-ghost {
            position: absolute; top: 50%; left: 50%;
            width: 170px; height: 170px; transform: translate(-50%, -50%);
            object-fit: contain; opacity: .15;
            filter: grayscale(40%) blur(1px); pointer-events: none; z-index: 0;
          }
          #${uid} .team-logo {
            position: relative; z-index: 1; width: 72px; height: 72px;
            object-fit: contain; filter: drop-shadow(0 4px 14px rgba(0,0,0,.7));
          }
          #${uid} .team-name {
            font-size: 11px; color: rgba(255,255,255,.55); text-align: center; line-height: 1.2;
          }
          #${uid} .center { text-align: center; flex: 0 0 auto; min-width: 96px; }
          #${uid} .channel-zone {
            display: flex; flex-direction: column; align-items: center; gap: 4px; margin-bottom: 6px;
          }
          #${uid} .channel-logo { max-width: 72px; max-height: 28px; object-fit: contain; }
          #${uid} .chaine { font-size: 12px; color: rgba(255,255,255,.4); }
          #${uid} .heure { font-size: 28px; font-weight: 800; color: #fff; }
          #${uid} .rug-footer {
            background: var(--rugby-footer-bg, rgba(0,0,0,0.45));
            border-top: 1px solid rgba(255,255,255,.07);
            padding: 11px 16px; text-align: center;
            color: var(--rugby-footer-color, #e63946);
            font-size: 16px; font-weight: 600; letter-spacing: .3px;
          }
          #${uid} .channel-zone {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            margin-bottom: 6px;
          }   
          #${uid} .channel-row {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
          }
          #${uid} .channel-logo {
            max-width: 72px;
            max-height: 28px;
            object-fit: contain;
          }
          #${uid} .chaine {
            font-size: 12px;
            color: rgba(255,255,255,.4);
          }
        </style>

        <div id="${uid}">
          <div class="rug-card">
            <div class="rug-top">
              <div class="rug-body">
                <div class="rug-game">
                  <span class="rug-game-name">${gameName}</span>
                  ${competition ? `<span class="rug-game-competition">${competition}</span>` : ""}
                </div>
                <div class="teams">
                  <div class="team-block">
                    <div class="team-logo-wrap">
                      ${logoDom ? `<img class="team-logo-ghost" src="${logoDom}">` : ""}
                      ${logoDom
                        ? `<img class="team-logo" src="${logoDom}">`
                        : `<div style="width:72px;height:72px"></div>`}
                    </div>
                    <span class="team-name">${b.domicile || ""}</span>
                  </div>
                  <div class="center">
                    ${diffuseur1 ? `
                       <div class="channel-zone">
                     
                         <div class="channel-row">
                           ${logoDiff1 ? `<img class="channel-logo" src="${logoDiff1}">` : ""}
                           <div class="chaine">${diffuseur1}</div>
                         </div>
                     
                         ${diffuseur2 ? `
                           <div class="channel-row">
                             ${logoDiff2 ? `<img class="channel-logo" src="${logoDiff2}">` : ""}
                             <div class="chaine">${diffuseur2}</div>
                           </div>
                         ` : ""}
                     
                       </div>
                     ` : `<div class="chaine">${state.state || ""}</div>`}
                  </div>
                  <div class="team-block">
                    <div class="team-logo-wrap">
                      ${logoExt ? `<img class="team-logo-ghost" src="${logoExt}">` : ""}
                      ${logoExt
                        ? `<img class="team-logo" src="${logoExt}">`
                        : `<div style="width:72px;height:72px"></div>`}
                    </div>
                    <span class="team-name">${b.exterieur || ""}</span>
                  </div>
                </div>
              </div>
            </div>
            ${date ? `<div class="rug-footer">${date}</div>` : ""}
          </div>
        </div>
      </ha-card>
    `;
  }

  static getConfigElement() {
    return document.createElement("rugby-lnr-game-card-editor");
  }

  static getStubConfig() {
    return { entity: "" };
  }

  getCardSize() { return 3; }
}

customElements.define("rugby-lnr-game-card", RugbyLnrGameCard);

/* ========================================================
   ÉDITEUR GRAPHIQUE
   ======================================================== */

class RugbyLnrGameCardEditor extends HTMLElement {

  constructor() {
    super();
    this._config = {};
    this._hass   = null;
    this.attachShadow({ mode: "open" });
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  setConfig(config) {
    this._config = config || {};
    this._render();
  }

  _render() {
    if (!this._hass) return;

    const entities = Object.keys(this._hass.states)
      .filter(e => e.startsWith("sensor.rugby_"))
      .sort();

    const current     = this._config?.entity       || "";
    const footerBg     = this._config?.footer_bg    || "rgba(0,0,0,0.45)";
    const footerColor  = this._config?.footer_color || "#e63946";

    const toHex = (c) => {
      if (!c || c.startsWith("rgba") || c.startsWith("rgb")) return "#000000";
      return c;
    };

    this.shadowRoot.innerHTML = `
      <style>
        .editor        { padding: 16px; display: flex; flex-direction: column; gap: 14px; }
        .field         { display: flex; flex-direction: column; gap: 4px; }
        label          { font-size: 13px; color: var(--primary-text-color, #fff); }
        select, input[type="text"] {
          width: 100%; padding: 8px 10px; border-radius: 8px;
          border: 1px solid rgba(255,255,255,.2);
          background: var(--card-background-color, #1e1e2e);
          color: var(--primary-text-color, #fff);
          font-size: 14px; cursor: pointer; box-sizing: border-box;
        }
        .color-row     { display: flex; align-items: center; gap: 10px; }
        input[type="color"] {
          width: 40px; height: 36px; border: none; border-radius: 8px;
          cursor: pointer; padding: 2px; background: transparent; flex-shrink: 0;
        }
        input[type="text"] { flex: 1; }
        .hint { font-size: 11px; color: rgba(255,255,255,.35); }
      </style>

      <div class="editor">
        <div class="field">
          <label>Sensor Rugby LNR</label>
          <select id="entity-select">
            <option value="">-- Choisir un sensor --</option>
            ${entities.map(e => `<option value="${e}" ${e === current ? "selected" : ""}>${e}</option>`).join("")}
          </select>
        </div>

        <div class="field">
          <label>Couleur de fond du bandeau</label>
          <div class="color-row">
            <input type="color" id="footer-bg-picker" value="${toHex(footerBg)}">
            <input type="text"  id="footer-bg-text"   value="${footerBg}" placeholder="ex: #1a1a2e ou rgba(0,0,0,0.5)">
          </div>
          <span class="hint">Valeur CSS acceptée : #hex, rgb(), rgba()</span>
        </div>

        <div class="field">
          <label>Couleur du texte du bandeau</label>
          <div class="color-row">
            <input type="color" id="footer-color-picker" value="${toHex(footerColor)}">
            <input type="text"  id="footer-color-text"   value="${footerColor}" placeholder="ex: #e63946">
          </div>
          <span class="hint">Valeur CSS acceptée : #hex, rgb(), rgba()</span>
        </div>
      </div>
    `;

    const fire = () => {
      this.dispatchEvent(new CustomEvent("config-changed", {
        bubbles: true, composed: true,
        detail: { config: this._config },
      }));
    };

    this.shadowRoot.getElementById("entity-select").addEventListener("change", (ev) => {
      if (!ev.target.value) return;
      this._config = { ...this._config, entity: ev.target.value };
      fire();
    });

    this.shadowRoot.getElementById("footer-bg-picker").addEventListener("input", (ev) => {
      this.shadowRoot.getElementById("footer-bg-text").value = ev.target.value;
      this._config = { ...this._config, footer_bg: ev.target.value };
      fire();
    });
    this.shadowRoot.getElementById("footer-bg-text").addEventListener("change", (ev) => {
      this._config = { ...this._config, footer_bg: ev.target.value };
      fire();
    });

    this.shadowRoot.getElementById("footer-color-picker").addEventListener("input", (ev) => {
      this.shadowRoot.getElementById("footer-color-text").value = ev.target.value;
      this._config = { ...this._config, footer_color: ev.target.value };
      fire();
    });
    this.shadowRoot.getElementById("footer-color-text").addEventListener("change", (ev) => {
      this._config = { ...this._config, footer_color: ev.target.value };
      fire();
    });
  }
}

customElements.define("rugby-lnr-game-card-editor", RugbyLnrGameCardEditor);
