const menuItems = [
  { label: "Spelunk", url: "spelunk.html" },
  { label: "YT Summary", url: "ytsummary_streamlit.html" },
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
  