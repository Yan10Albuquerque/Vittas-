window.menuUnidade = function () {
  const getCookie = (name) => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      return parts.pop().split(";").shift();
    }
    return "";
  };

  return {
    async onChange(event) {
      const select = event.target;
      if (!select || select.hasAttribute("disabled")) {
        return;
      }

      const url = select.dataset.url;
      if (!url) {
        return;
      }

      const formData = new URLSearchParams({ unidade: select.value });
      try {
        const response = await fetch(url, {
          method: "POST",
          headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: formData,
        });
        const data = await response.json();
        if (!response.ok || data.status !== "OK") {
          throw new Error(data.message || "Falha ao atualizar unidade.");
        }
        window.location.reload();
      } catch (error) {
        window.dispatchEvent(
          new CustomEvent("show-toast", {
            detail: {
              type: "error",
              message: error.message || "Falha ao atualizar unidade.",
            },
          })
        );
      }
    },
  };
};
