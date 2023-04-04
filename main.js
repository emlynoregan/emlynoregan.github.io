const menuItems = [
    { label: "Home", url: "index.html" },
    { label: "The Metal Wizard", url: "themetalwizard.html" },
    { label: "Sutllang", url: "sutllang.html" },
    { label: "YouTube Summarizer", url: "ytsummary_streamlit.html" },
  ];
  
  const header = document.getElementById("header");
  const footer = document.getElementById("footer");
  
  header.innerHTML = `
    <h1><a href="/">emlynoregan.com</a></h1>
    <nav>
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
    <p>This website was created by ChatGPT using JavaScript.</p>
  `;
  