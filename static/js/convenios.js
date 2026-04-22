window.convenioCrud = function () {
  const getCookie = (name) => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      return parts.pop().split(";").shift();
    }
    return "";
  };

  return {
    modalHtml: "",
    modalTitle: "Cadastro",
    activeUrl: "",
    isModalLoading: false,
    isSubmitting: false,
    csrfToken: "",

    init() {
      this.csrfToken = this.getCsrfToken();
    },

    getCsrfToken() {
      const input = this.$root.querySelector("[name=csrfmiddlewaretoken]");
      if (input && input.value) {
        return input.value;
      }
      return getCookie("csrftoken");
    },

    async openModal(url) {
      this.activeUrl = url;
      this.modalTitle = url.includes("editar")
        ? "Editar Convênio"
        : "Novo Convênio";
      this.isModalLoading = true;
      this.modalHtml = "";

      if (this.$refs.modal) {
        this.$refs.modal.showModal();
      }

      await this.fetchForm(url);
    },

    closeModal() {
      if (this.$refs.modal && this.$refs.modal.open) {
        this.$refs.modal.close();
      }
    },

    async fetchForm(url) {
      try {
        const response = await fetch(url, {
          headers: { "X-Requested-With": "XMLHttpRequest" },
        });
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        this.modalHtml = await response.text();
        this.refreshModalContent();
      } catch (error) {
        this.modalHtml =
          '<div class="alert alert-error"><i class="fas fa-exclamation-triangle"></i> Erro ao carregar o formulário. Tente novamente.</div>';
        this.refreshModalContent();
        console.error("Error fetching form:", error);
      } finally {
        this.isModalLoading = false;
      }
    },

    refreshModalContent() {
      this.$nextTick(() => {
        if (window.Alpine && this.$refs.modalContent) {
          window.Alpine.initTree(this.$refs.modalContent);
        }
      });
    },

    async submitForm(formElement) {
      this.isSubmitting = true;
      const formData = new FormData(formElement);

      try {
        const response = await fetch(this.activeUrl, {
          method: "POST",
          body: formData,
          headers: { "X-Requested-With": "XMLHttpRequest" },
        });

        const data = await response.json();

        if (data.success) {
          this.closeModal();
          
          // Usa o toast global
          window.dispatchEvent(new CustomEvent('show-toast', {
            detail: {
              type: 'success',
              message: 'Convênio salvo com sucesso!'
            }
          }));
          
          setTimeout(() => {
            window.location.reload();
          }, 1500);
        } else if (data.html) {
          this.modalHtml = data.html;
          this.refreshModalContent();
        } else {
          this.closeModal();
          
          window.dispatchEvent(new CustomEvent('show-toast', {
            detail: {
              type: 'error',
              message: 'Falha ao salvar o convênio. Verifique os dados e tente novamente.'
            }
          }));
        }
      } catch (error) {
        console.error(error);
        this.closeModal();
        
        window.dispatchEvent(new CustomEvent('show-toast', {
          detail: {
            type: 'error',
            message: 'Erro de conexão ao salvar. Verifique sua internet e tente novamente.'
          }
        }));
      } finally {
        this.isSubmitting = false;
      }
    },

    deleteItem(url) {
      // Usa o dialog global de confirmação
      window.openConfirmDialog(url, () => {
        // Callback após exclusão bem-sucedida
        window.dispatchEvent(new CustomEvent('show-toast', {
          detail: {
            type: 'success',
            message: 'Convênio excluído com sucesso!'
          }
        }));

        setTimeout(() => {
          window.location.reload();
        }, 1500);
      });
    },
  };
};
