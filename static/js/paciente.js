function pacienteFormCep(initialTab = 'cadastro') {
  return {
    activeTab: initialTab || 'cadastro',
    consultandoCep: false,

    init() {
      const cepInput = document.getElementById('id_cep');
      if (!cepInput) {
        return;
      }

      cepInput.addEventListener('blur', () => {
        this.buscarCep();
      });
    },

    async buscarCep() {
      const cepInput = document.getElementById('id_cep');
      if (!cepInput) {
        return;
      }

      const cepLimpo = (cepInput.value || '').replace(/\D/g, '');
      if (cepLimpo.length !== 8) {
        return;
      }

      this.consultandoCep = true;

      try {
        const response = await fetch(`/pacientes/api/cep/${cepLimpo}`, {
          method: 'GET',
          headers: {
            Accept: 'application/json'
          }
        });

        if (!response.ok) {
          return;
        }

        const payload = await response.json();
        if (!payload.success || !payload.data) {
          return;
        }

        const { street, neighborhood, city, state } = payload.data;

        const logradouroInput = document.getElementById('id_logradouro');
        const bairroInput = document.getElementById('id_bairro');
        const cidadeInput = document.getElementById('id_cidade');
        const estadoInput = document.getElementById('id_estado');

        if (logradouroInput) {
          logradouroInput.value = street || '';
        }
        if (bairroInput) {
          bairroInput.value = neighborhood || '';
        }
        if (cidadeInput) {
          cidadeInput.value = city || '';
        }
        if (estadoInput && state) {
          estadoInput.value = state;
        }
      } catch (error) {
      } finally {
        this.consultandoCep = false;
      }
    }
  };
}

window.pacienteFormCep = pacienteFormCep;