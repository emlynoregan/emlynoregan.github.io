const menuItems = [
  { label: "PDF Editor", url: "pdfeditor.html" },
  { label: "Flappy Bird", url: "flappybird.html" },
  { label: "Space Invaders", url: "spaceinvaders.html" },
  { label: "Orc Simulator", url: "orcsimulator.html" },
  { label: "Metal Wizard", url: "themetalwizard.html" },
    { label: "sUTL", url: "sutllang.html" },
  ];
  
  const header = document.getElementById("header");
  const footer = document.getElementById("footer");
  
  header.innerHTML = `
    <div class="site-title">
      <h1><a href="/">emlynoregan.com</a></h1>
    </div>
      <nav class="site-nav">
        <ul>
          ${menuItems
            .map(
              (menuItem) =>
                `<li><a href="${menuItem.url}">${menuItem.label}</a></li>`
            )
            .join("")}
        </ul>
      </nav>
  `;
  
  const year = new Date().getFullYear();
  footer.innerHTML = `
    <p>© ${year} Emlyn O'Regan. All rights reserved.</p>
    <p>This website was created in conversation with ChatGPT.</p>
  `;
  