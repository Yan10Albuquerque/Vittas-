window.getCookie = window.getCookie || function (name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop().split(";").shift();
  }
  return "";
};

window.showToast = window.showToast || function (type, message) {
  window.dispatchEvent(
    new CustomEvent("show-toast", {
      detail: { type, message },
    })
  );
};

window.menuUnidade = function () {
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
            "X-CSRFToken": window.getCookie("csrftoken"),
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
        window.showToast("error", error.message || "Falha ao atualizar unidade.");
      }
    },
  };
};

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-logout-form]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();

      try {
        const response = await fetch(form.action, {
          method: "POST",
          headers: {
            "X-CSRFToken": window.getCookie("csrftoken"),
            "X-Requested-With": "XMLHttpRequest",
          },
        });
        const data = await response.json();
        if (!response.ok || data.status !== "OK") {
          throw new Error(data.message || "Não foi possível sair do sistema.");
        }
        window.location.href = data.redirect_url || "/login/";
      } catch (error) {
        window.showToast("error", error.message || "Não foi possível sair do sistema.");
      }
    });
  });

  const changePasswordButton = document.getElementById("alterar_senha_user");
  if (changePasswordButton) {
    changePasswordButton.addEventListener("click", async () => {
      const currentPasswordInput = document.getElementById("senha_atual_user");
      const newPasswordInput = document.getElementById("nova_senha_user");
      const currentPassword = currentPasswordInput ? currentPasswordInput.value : "";
      const newPassword = newPasswordInput ? newPasswordInput.value : "";

      if (!currentPassword || !newPassword) {
        window.showToast("warning", "Informe a senha atual e a nova senha.");
        return;
      }

      changePasswordButton.disabled = true;
      const originalHtml = changePasswordButton.innerHTML;
      changePasswordButton.innerHTML = '<span class="loading loading-spinner loading-xs"></span> Alterando...';

      try {
        const response = await fetch(changePasswordButton.dataset.url, {
          method: "POST",
          headers: {
            "X-CSRFToken": window.getCookie("csrftoken"),
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: new URLSearchParams({
            senha_atual: currentPassword,
            nova_senha: newPassword,
          }),
        });
        const data = await response.json();
        if (!response.ok || data.status !== "OK") {
          throw new Error(data.message || "Não foi possível alterar a senha.");
        }

        if (currentPasswordInput) {
          currentPasswordInput.value = "";
        }
        if (newPasswordInput) {
          newPasswordInput.value = "";
        }
        document.getElementById("modal_perfil")?.classList.remove("modal-open");
        window.showToast("success", "Senha alterada com sucesso.");
      } catch (error) {
        window.showToast("error", error.message || "Não foi possível alterar a senha.");
      } finally {
        changePasswordButton.disabled = false;
        changePasswordButton.innerHTML = originalHtml;
      }
    });
  }
});
