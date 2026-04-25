window.agendaConsultasPage = function () {
  const normalizeText = (value) => (value || "").toString().trim().toLowerCase();

  const getCookie = (name) => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      return parts.pop().split(";").shift();
    }
    return "";
  };

  const formatDateBr = (value) => {
    if (!value) {
      return "";
    }

    const [year, month, day] = value.split("-");
    if (!year || !month || !day) {
      return value;
    }

    return `${day}/${month}/${year}`;
  };

  return {
    endpoints: {
      schedule: "",
      patient: "",
    },

    init() {
      this.root = this.$el;
      this.csrfToken = getCookie("csrftoken");
      this.endpoints.schedule = this.root.dataset.scheduleUrl || "";
      this.endpoints.patient = this.root.dataset.patientUrl || "";
      this.endpoints.medicoEspecialidadesTemplate = this.root.dataset.medicoEspecialidadesUrlTemplate || "";
      this.statusEmAtendimentoId = this.root.dataset.statusEmAtendimentoId || "";
      this.form = this.root.querySelector("#form_medico");
      this.consultasBody = this.root.querySelector("#consultas");
      this.codMedicoInput = this.root.querySelector("#cod_medico");
      this.dataAgendaInput = this.root.querySelector("#data_agenda");
      this.modalPacientes = this.root.querySelector("#modal_pacientes");
      this.modalConsulta = this.root.querySelector("#modal_consulta");
      this.modalStatus = this.root.querySelector("#modalStatus");
      this.modalCadBasico = this.root.querySelector("#modal_cadbasico");
      this.modalCadCompleto = this.root.querySelector("#modal_cadcompleto");
      this.modalAddHora = this.root.querySelector("#modal_addhora");

      this.bindEvents();
      this.updateSelectedDoctor();
      this.updateAgeLabel();
    },

    bindEvents() {
      this.root.addEventListener("click", (event) => {
        const target = event.target.closest("[data-action]");
        if (!target) {
          return;
        }

        const action = target.dataset.action;
        switch (action) {
          case "selecionar-medico":
            event.preventDefault();
            this.selectDoctor(target);
            break;
          case "dia-anterior":
          case "dia-proximo":
            event.preventDefault();
            this.navigateDay(target);
            break;
          case "agendar-horario":
            event.preventDefault();
            this.handleHourButton(target);
            break;
          case "pesquisar-paciente":
            event.preventDefault();
            this.searchPatients();
            break;
          case "continuar-consulta":
            event.preventDefault();
            this.continueToConsulta();
            break;
          case "salvar-consulta":
            event.preventDefault();
            this.saveConsulta(target);
            break;
          case "alterar-status":
            event.preventDefault();
            this.openStatusModal(target);
            break;
          case "definir-status":
            event.preventDefault();
            this.updateStatus(target);
            break;
          case "abrir-cadastro-basico":
            event.preventDefault();
            this.prefillCadastroBasico();
            this.switchModal(target, target.dataset.modalTarget);
            break;
          case "salvar-cadastro-basico":
            event.preventDefault();
            this.saveCadastroBasico(target);
            break;
          case "continuar-cadastro-basico":
            event.preventDefault();
            this.continueCadastroBasico();
            break;
          case "voltar-pacientes":
            event.preventDefault();
            this.switchModal(target, target.dataset.modalTarget);
            break;
          case "bloquear-horario":
            event.preventDefault();
            this.blockHorario(target);
            break;
          case "preparar-novo-horario":
            event.preventDefault();
            this.prepareNovoHorario(target);
            break;
          case "adicionar-horario":
            event.preventDefault();
            this.addHorario(target);
            break;
          case "abrir-agenda":
            event.preventDefault();
            this.addAgenda(target);
            break;
          case "confirmar-cadastro-completo":
            event.preventDefault();
            this.confirmCadastroCompleto(target);
            break;
          case "abrir-modal":
            event.preventDefault();
            this.switchModal(target, target.dataset.modalTarget);
            break;
          default:
            break;
        }
      });

      this.root.addEventListener("change", (event) => {
        if (event.target.id === "data_agenda") {
          this.changeAgendaDate();
          return;
        }

        if (event.target.closest("#modal_cadcompleto")) {
          this.clearFieldValidation(event.target);
        }

        if (event.target.classList.contains("selecionado")) {
          this.selectPaciente(event.target);
        }
      });

      this.root.addEventListener("input", (event) => {
        if (event.target.closest("#modal_cadcompleto")) {
          this.clearFieldValidation(event.target);
        }
      });

      this.root.addEventListener(
        "blur",
        (event) => {
          if (event.target.id === "nascimento") {
            this.updateAgeLabel();
          }

          if (event.target.id === "cep") {
            this.fillAddressFromCep();
          }
        },
        true
      );
    },

    query(selector) {
      return this.root.querySelector(selector);
    },

    updateSelectedDoctor() {
      const activeButton = this.root.querySelector("[data-action='selecionar-medico'].btn-active");
      this.selectedDoctorId = this.codMedicoInput ? this.codMedicoInput.value : "";
      this.selectedDoctorName = activeButton ? activeButton.dataset.medicoNome : "";
    },

    getMedicoEspecialidadesUrl(medicoId) {
      if (!this.endpoints.medicoEspecialidadesTemplate || !medicoId) {
        return "";
      }
      return this.endpoints.medicoEspecialidadesTemplate.replace("/0/", `/${medicoId}/`);
    },

    async loadEspecialidadesMedico() {
      const select = this.query("#especialidade_consulta");
      if (!select) {
        return true;
      }

      select.innerHTML = "<option value=''>Carregando...</option>";
      const url = this.getMedicoEspecialidadesUrl(this.selectedDoctorId);
      if (!url) {
        select.innerHTML = "<option value=''>Selecione</option>";
        return false;
      }

      try {
        const response = await fetch(url, {
          headers: {
            "X-Requested-With": "XMLHttpRequest",
          },
        });
        const data = await response.json();
        if (!response.ok || !data.success) {
          throw new Error(data.message || "Nao foi possivel carregar as especialidades.");
        }

        if (!data.especialidades.length) {
          select.innerHTML = "<option value=''>Sem especialidades cadastradas</option>";
          return false;
        }

        select.innerHTML = ["<option value=''>Selecione</option>"]
          .concat(
            data.especialidades.map(
              (item) => `<option value='${item.id}'>${item.descricao}</option>`
            )
          )
          .join("");
        return true;
      } catch (error) {
        select.innerHTML = "<option value=''>Selecione</option>";
        this.showToast("error", error.message || "Falha ao carregar especialidades.");
        return false;
      }
    },

    showToast(type, message) {
      const modalAberto = this.root.querySelector("dialog[open]");
      if (modalAberto) {
        this.showModalAlert(modalAberto, type, message);
        return;
      }

      window.dispatchEvent(
        new CustomEvent("show-toast", {
          detail: { type, message },
        })
      );
    },

    requestConfirmation(options) {
      if (typeof window.openConfirmDialog !== "function") {
        this.showToast("error", "Nao foi possivel abrir o dialogo de confirmacao.");
        return Promise.resolve(false);
      }

      return new Promise((resolve) => {
        window.openConfirmDialog({
          title: options?.title || "Confirmar acao",
          message: options?.message || "Confirma esta acao?",
          detail: options?.detail || "",
          confirmLabel: options?.confirmLabel || "Confirmar",
          confirmIcon: options?.confirmIcon || "fas fa-check",
          confirmButtonClass: options?.confirmButtonClass || "btn-primary",
          onConfirm: async () => {
            resolve(true);
          },
          onCancel: () => {
            resolve(false);
          },
        });
      });
    },

    showModalAlert(modal, type, message) {
      const modalAction = modal.querySelector(".modal-action");
      const modalBox = modal.querySelector(".modal-box");
      const container = modalAction || modalBox;
      if (!container) {
        return;
      }

      const previous = modal.querySelector("[data-modal-alert]");
      if (previous) {
        previous.remove();
      }

      const classesByType = {
        success: "alert-success",
        error: "alert-error",
        warning: "alert-warning",
        info: "alert-info",
      };

      const alert = document.createElement("div");
      alert.setAttribute("data-modal-alert", "1");
      alert.className = `alert ${classesByType[type] || "alert-info"} w-full mb-2`;

      const content = document.createElement("span");
      content.textContent = message || "";
      alert.appendChild(content);

      container.parentNode.insertBefore(alert, container);

      window.setTimeout(() => {
        alert.remove();
      }, 5000);
    },

    clearFieldValidation(field) {
      if (!field || !field.id) {
        return;
      }

      field.classList.remove("input-error", "select-error", "textarea-error");

      const error = this.root.querySelector(`[data-field-error='${field.id}']`);
      if (error) {
        error.remove();
      }
    },

    markFieldInvalid(field, message) {
      if (!field || !field.id) {
        return;
      }

      const tagName = (field.tagName || "").toUpperCase();
      if (tagName === "SELECT") {
        field.classList.add("select-error");
      } else if (tagName === "TEXTAREA") {
        field.classList.add("textarea-error");
      } else {
        field.classList.add("input-error");
      }

      const existingError = this.root.querySelector(`[data-field-error='${field.id}']`);
      if (existingError) {
        existingError.textContent = message;
        return;
      }

      const error = document.createElement("p");
      error.setAttribute("data-field-error", field.id);
      error.className = "text-error text-xs mt-1";
      error.textContent = message;
      field.insertAdjacentElement("afterend", error);
    },

    clearCadastroCompletoValidation() {
      const fields = this.root.querySelectorAll(
        "#modal_cadcompleto input[id], #modal_cadcompleto select[id], #modal_cadcompleto textarea[id]"
      );

      fields.forEach((field) => {
        this.clearFieldValidation(field);
      });
    },

    showAgendaLoading() {
      if (!this.consultasBody) {
        return;
      }

      this.consultasBody.innerHTML = "<tr><td colspan='6' class='py-6 text-center'><span class='loading loading-spinner loading-md'></span></td></tr>";
    },

    showAgendaMessage(message) {
      if (!this.consultasBody) {
        return;
      }

      this.consultasBody.innerHTML = `<tr><td colspan='6' class='py-6 text-center text-base-content/70'>${message}</td></tr>`;
    },

    selectDoctor(button) {
      const url = button.getAttribute("href");
      if (!url) {
        return;
      }

      this.showAgendaLoading();
      window.location.href = url;
    },

    navigateDay(button) {
      this.updateSelectedDoctor();
      if (!this.selectedDoctorId || this.selectedDoctorId === "0") {
        this.showAgendaMessage("SELECIONE UM MEDICO PARA VISUALIZAR A AGENDA");
        this.showToast("warning", "Selecione um medico para visualizar a agenda.");
        return;
      }

      const url = button.getAttribute("formaction");
      if (!url) {
        return;
      }

      this.showAgendaLoading();
      window.location.href = url;
    },

    changeAgendaDate() {
      this.updateSelectedDoctor();
      if (!this.selectedDoctorId || this.selectedDoctorId === "0") {
        this.showAgendaMessage("SELECIONE UM MEDICO PARA VISUALIZAR A AGENDA");
        this.showToast("warning", "Selecione um medico antes de alterar a data.");
        return;
      }

      if (!this.form || !this.dataAgendaInput || !this.codMedicoInput) {
        return;
      }

      this.codMedicoInput.value = this.selectedDoctorId;
      this.showAgendaLoading();
      this.form.submit();
    },

    handleHourButton(button) {
      if (button.classList.contains("cancelar_consulta")) {
        this.cancelConsulta(button);
        return;
      }

      if (button.classList.contains("liberar")) {
        this.releaseHorario(button);
        return;
      }

      this.openAgendamento(button);
    },

    async openAgendamento(button) {
      this.updateSelectedDoctor();
      if (!this.selectedDoctorId || this.selectedDoctorId === "0") {
        this.showToast("warning", "Selecione um medico antes de agendar.");
        return;
      }

      const possuiEspecialidades = await this.loadEspecialidadesMedico();
      if (!possuiEspecialidades) {
        this.showToast("warning", "O medico selecionado nao possui especialidades ativas para agendamento.");
        return;
      }

      const hora = button.textContent.trim();
      const dataAgendaBr = formatDateBr(this.dataAgendaInput ? this.dataAgendaInput.value : "");
      const tituloPacientes = this.query("#titulo_modal_pacientes");
      const tituloConsulta = this.query("#titulo_modal_consulta");
      const codAgendaConsulta = this.query("#cod_agenda_consulta");
      const codMedicoConsulta = this.query("#cod_medico_consulta");
      const nomeMedicoConsulta = this.query("#nome_medico_consulta");
      const dataAgendaConsulta = this.query("#data_agenda_consulta");
      const horaConsulta = this.query("#hora_consulta");
      const codPacienteConsulta = this.query("#cod_paciente_consulta");
      const nomePacienteConsulta = this.query("#nome_paciente_consulta");

      if (tituloPacientes) {
        tituloPacientes.innerHTML = `Paciente para Consulta: <span class='text-error'>${dataAgendaBr} as ${hora}</span>`;
      }
      if (tituloConsulta) {
        tituloConsulta.innerHTML = `Agendamento de Consulta: <span class='text-error'>${dataAgendaBr} as ${hora}</span>`;
      }

      this.root.querySelectorAll(".bloquear").forEach((element) => {
        element.value = hora;
      });

      if (codAgendaConsulta) {
        codAgendaConsulta.value = button.value || "";
      }
      if (codMedicoConsulta) {
        codMedicoConsulta.value = this.selectedDoctorId;
      }
      if (nomeMedicoConsulta) {
        nomeMedicoConsulta.value = this.selectedDoctorName;
      }
      if (dataAgendaConsulta && this.dataAgendaInput) {
        dataAgendaConsulta.value = this.dataAgendaInput.value;
      }
      if (horaConsulta) {
        horaConsulta.value = hora;
      }
      if (codPacienteConsulta) {
        codPacienteConsulta.value = "";
      }
      if (nomePacienteConsulta) {
        nomePacienteConsulta.value = "";
      }

      this.openModal(this.modalPacientes);
    },

    switchModal(source, targetId) {
      if (!targetId) {
        return;
      }

      const currentDialog = source.closest("dialog");
      if (currentDialog) {
        currentDialog.close();
      }

      const targetDialog = this.root.querySelector(`#${targetId}`);
      this.openModal(targetDialog);
    },

    openModal(modal) {
      if (modal && typeof modal.showModal === "function") {
        modal.showModal();
      }
    },

    closeModal(modal) {
      if (modal && typeof modal.close === "function") {
        modal.close();
      }
    },

    searchPatients() {
      const cpf = normalizeText(this.query("#pesqcpf")?.value);
      const nome = normalizeText(this.query("#pesqnome")?.value);
      const celular = normalizeText(this.query("#pesqcelular")?.value);
      const rows = Array.from(this.root.querySelectorAll("#pacientes tr[data-paciente-id]"));

      if (!rows.length) {
        return;
      }

      rows.forEach((row) => {
        const cells = row.querySelectorAll("td");
        const rowCpf = normalizeText(cells[1]?.textContent);
        const rowNome = normalizeText(cells[2]?.textContent);
        const rowCelular = normalizeText(cells[3]?.textContent);

        const matchesCpf = !cpf || rowCpf.includes(cpf);
        const matchesNome = !nome || rowNome.includes(nome);
        const matchesCelular = !celular || rowCelular.includes(celular);

        row.classList.toggle("hidden", !(matchesCpf && matchesNome && matchesCelular));
      });
    },

    selectPaciente(radio) {
      const row = radio.closest("tr");
      if (!row) {
        return;
      }

      const cells = row.querySelectorAll("td");
      const pacienteId = radio.value;
      const pacienteNome = cells[2]?.textContent.trim() || "";
      const convenioId = cells[4]?.dataset.convenioId || "";

      const codPacienteConsulta = this.query("#cod_paciente_consulta");
      const nomePacienteConsulta = this.query("#nome_paciente_consulta");
      const convenioConsulta = this.query("#convenio_consulta");

      if (codPacienteConsulta) {
        codPacienteConsulta.value = pacienteId;
      }
      if (nomePacienteConsulta) {
        nomePacienteConsulta.value = pacienteNome;
      }
      if (convenioConsulta && convenioId) {
        convenioConsulta.value = convenioId;
      }
    },

    continueToConsulta() {
      const codPacienteConsulta = this.query("#cod_paciente_consulta");
      if (!codPacienteConsulta || !codPacienteConsulta.value) {
        this.showToast("warning", "Selecione o paciente antes de continuar.");
        return;
      }

      this.closeModal(this.modalPacientes);
      this.openModal(this.modalConsulta);
    },

    validateConsulta() {
      const codAgenda = this.query("#cod_agenda_consulta")?.value;
      const especialidade = this.query("#especialidade_consulta")?.value;
      const codPaciente = this.query("#cod_paciente_consulta")?.value;
      const tipoConsulta = this.query("#tipo_consulta")?.value;

      if (!codAgenda) {
        this.showToast("error", "Erro ao localizar o codigo da agenda.");
        return false;
      }
      if (!especialidade) {
        this.showToast("warning", "Selecione uma especialidade.");
        return false;
      }
      if (!codPaciente) {
        this.showToast("warning", "Selecione o paciente antes de continuar.");
        return false;
      }
      if (!tipoConsulta) {
        this.showToast("warning", "Informe o tipo de consulta.");
        return false;
      }

      return true;
    },

    async saveConsulta(button) {
      if (!this.validateConsulta()) {
        return;
      }

      if (!this.endpoints.schedule) {
        this.showToast("info", "Endpoint de agenda ainda nao configurado no backend Django.");
        return;
      }

      const payload = {
        funcao: "salvar_consulta",
        cod_agenda: this.query("#cod_agenda_consulta")?.value || "",
        data_agenda: this.query("#data_agenda_consulta")?.value || "",
        hora_consulta: this.query("#hora_consulta")?.value || "",
        nome_medico: this.query("#nome_medico_consulta")?.value || "",
        cod_paciente: this.query("#cod_paciente_consulta")?.value || "",
        nome_paciente: this.query("#nome_paciente_consulta")?.value || "",
        convenio_consulta: this.query("#convenio_consulta")?.value || "",
        cod_tipo_consulta: this.query("#tipo_consulta")?.value || "",
        cod_especialidade: this.query("#especialidade_consulta")?.value || "",
        cod_status_agendamento: this.query("#status_agendamento_consulta")?.value || "",
      };

      await this.postAction(button, this.endpoints.schedule, payload, {
        successMessage: "Consulta salva com sucesso.",
        reloadOnSuccess: true,
        loadingHtml: "<span class='loading loading-spinner loading-xs'></span>",
      });
    },

    async cancelConsulta(button) {
      const codAgenda = button.value;
      const hora = button.textContent.trim();
      const dataAgenda = formatDateBr(this.dataAgendaInput?.value || "");
      const nomePaciente = this.query(`#paciente${codAgenda}`)?.textContent.trim() || "paciente";

      const confirmed = await this.requestConfirmation({
        title: "Cancelar consulta",
        message: `Confirma o cancelamento da consulta de ${nomePaciente} em ${dataAgenda} as ${hora}?`,
        detail: "O horario voltara a ficar disponivel na agenda.",
        confirmLabel: "Cancelar consulta",
        confirmIcon: "fas fa-calendar-xmark",
        confirmButtonClass: "btn-error",
      });

      if (!confirmed) {
        return;
      }

      if (!this.endpoints.schedule) {
        this.showToast("info", "Endpoint de cancelamento ainda nao configurado.");
        return;
      }

      this.postAction(button, this.endpoints.schedule, {
        funcao: "cancelar_consulta",
        cod_agenda: codAgenda,
      }, {
        successMessage: "Consulta cancelada com sucesso.",
        reloadOnSuccess: true,
      });
    },

    async blockHorario(button) {
      const codAgenda = this.query("#cod_agenda_consulta")?.value || this.query("#cod_agenda_status")?.value || "";
      const hora = button.value || this.query("#hora_consulta")?.value || "";
      const dataAgenda = formatDateBr(this.dataAgendaInput?.value || "");

      const confirmed = await this.requestConfirmation({
        title: "Bloquear horario",
        message: `Confirma o bloqueio do horario ${hora} do dia ${dataAgenda}?`,
        detail: "Esse horario deixara de aparecer como disponivel para novos agendamentos.",
        confirmLabel: "Bloquear horario",
        confirmIcon: "fas fa-ban",
        confirmButtonClass: "btn-warning",
      });

      if (!confirmed) {
        return;
      }

      if (!this.endpoints.schedule) {
        this.showToast("info", "Endpoint de bloqueio ainda nao configurado.");
        return;
      }

      this.postAction(button, this.endpoints.schedule, {
        funcao: "bloquear_horario",
        cod_agenda: codAgenda,
      }, {
        successMessage: "Horario bloqueado com sucesso.",
        reloadOnSuccess: true,
      });
    },

    async releaseHorario(button) {
      const codAgenda = button.value;
      const hora = button.textContent.trim();
      const dataAgenda = formatDateBr(this.dataAgendaInput?.value || "");

      const confirmed = await this.requestConfirmation({
        title: "Liberar horario",
        message: `Confirma a liberacao do horario ${hora} do dia ${dataAgenda}?`,
        detail: "O horario voltara a aceitar novos agendamentos.",
        confirmLabel: "Liberar horario",
        confirmIcon: "fas fa-lock-open",
        confirmButtonClass: "btn-primary",
      });

      if (!confirmed) {
        return;
      }

      if (!this.endpoints.schedule) {
        this.showToast("info", "Endpoint de liberacao ainda nao configurado.");
        return;
      }

      this.postAction(button, this.endpoints.schedule, {
        funcao: "liberar_horario",
        cod_agenda: codAgenda,
      }, {
        successMessage: "Horario liberado com sucesso.",
        reloadOnSuccess: true,
      });
    },

    openStatusModal(button) {
      const codStatusConsulta = button.dataset.codstatusconsulta;
      const codAgenda = button.value;
      const hora = this.query(`#horaConsulta${codAgenda}`)?.textContent.trim() || "";
      const dataAgenda = formatDateBr(this.dataAgendaInput?.value || "");

      const codAgendaStatus = this.query("#cod_agenda_status");
      const titleModalStatus = this.query("#title_modal_status");
      if (codAgendaStatus) {
        codAgendaStatus.value = codAgenda;
      }
      if (titleModalStatus) {
        titleModalStatus.textContent = `${dataAgenda} as ${hora}`;
      }
      this.openModal(this.modalStatus);
    },

    async updateStatus(button) {
      const codAgendaStatus = this.query("#cod_agenda_status")?.value || "";
      const codNovoStatus = button.value;
      const originalHtml = button.innerHTML;

      if (String(codNovoStatus) === "3") {
        this.closeModal(this.modalStatus);
        await this.loadCadastroCompleto();
        return;
      }

      if (!this.endpoints.schedule) {
        this.showToast("info", "Endpoint de status ainda nao configurado.");
        return;
      }

      await this.postAction(button, this.endpoints.schedule, {
        funcao: "novo_status",
        cod_agenda: codAgendaStatus,
        cod_novo_status: codNovoStatus,
      }, {
        successMessage: "Status atualizado com sucesso.",
        reloadOnSuccess: true,
        loadingHtml: "<span class='loading loading-spinner loading-xs'></span>",
        restoreHtml: originalHtml,
      });
    },

    prefillCadastroBasico() {
      const nome = this.query("#pesqnome")?.value || "";
      const celular = this.query("#pesqcelular")?.value || "";
      const cpf = this.query("#pesqcpf")?.value || "";

      if (this.query("#nome_cadbasico")) {
        this.query("#nome_cadbasico").value = nome;
      }
      if (this.query("#celular_cadbasico")) {
        this.query("#celular_cadbasico").value = celular;
      }
      if (this.query("#cpf_cadbasico")) {
        this.query("#cpf_cadbasico").value = cpf;
      }
      if (this.query("#resposta_cadbasico")) {
        this.query("#resposta_cadbasico").textContent = "";
      }
      this.query("#salvar_cadbasico")?.classList.remove("hidden");
      this.query("#continuar_cadbasico")?.classList.add("hidden");
    },

    async saveCadastroBasico(button) {
      const celular = this.query("#celular_cadbasico")?.value || "";
      if (!celular) {
        this.showToast("warning", "Informe o celular para continuar.");
        return;
      }

      if (!this.endpoints.patient) {
        this.showToast("info", "Endpoint de cadastro basico ainda nao configurado.");
        return;
      }

      const payload = {
        funcao: "cadbasico",
        cpf: this.query("#cpf_cadbasico")?.value || "",
        nome: this.query("#nome_cadbasico")?.value || "",
        celular,
        nascimento: "1900-01-01",
        convenio: this.query("#convenio_cadbasico")?.value || "",
      };

      const response = await this.postAction(button, this.endpoints.patient, payload, {
        loadingHtml: "<span class='loading loading-spinner loading-xs'></span>",
      });

      if (!response) {
        return;
      }

      if (this.query("#cod_paciente_cadbasico")) {
        this.query("#cod_paciente_cadbasico").value = response.paciente_id || "";
      }
      if (this.query("#resposta_cadbasico")) {
        this.query("#resposta_cadbasico").textContent = `(${response.paciente_id || ""})`;
      }
      button.classList.add("hidden");
      this.query("#continuar_cadbasico")?.classList.remove("hidden");
    },

    continueCadastroBasico() {
      const codPaciente = this.query("#cod_paciente_cadbasico")?.value || "";
      if (!codPaciente) {
        this.showToast("warning", "Conclua o cadastro basico antes de continuar.");
        return;
      }

      if (this.query("#cod_paciente_consulta")) {
        this.query("#cod_paciente_consulta").value = codPaciente;
      }
      if (this.query("#nome_paciente_consulta")) {
        this.query("#nome_paciente_consulta").value = this.query("#nome_cadbasico")?.value || "";
      }
      if (this.query("#convenio_consulta")) {
        this.query("#convenio_consulta").value = this.query("#convenio_cadbasico")?.value || "";
      }

      this.closeModal(this.modalCadBasico);
      this.openModal(this.modalConsulta);
    },

    updateAgeLabel() {
      const nascimento = this.query("#nascimento")?.value || "";
      const idadeLabel = this.query("#idade");
      if (!idadeLabel) {
        return;
      }

      if (!nascimento || nascimento.length < 4) {
        idadeLabel.textContent = "";
        return;
      }

      const ano = Number(nascimento.slice(0, 4));
      const idade = new Date().getFullYear() - ano;
      idadeLabel.textContent = Number.isFinite(idade) ? `(${idade} anos)` : "";
    },

    async fillAddressFromCep() {
      const cep = this.query("#cep")?.value || "";
      if (!cep) {
        return;
      }

      const label = this.query("#label_cep");
      if (label) {
        label.innerHTML = "CEP <span class='loading loading-spinner loading-xs'></span>";
      }

      try {
        const response = await fetch(`https://brasilapi.com.br/api/cep/v2/${cep}`);
        if (!response.ok) {
          throw new Error("CEP nao encontrado.");
        }

        const data = await response.json();
        this.query("#endereco").value = data.street || "";
        this.query("#bairro").value = data.neighborhood || "";
        this.query("#cidade").value = data.city || "";
        this.query("#estado").value = data.state || "";
      } catch (error) {
        this.showToast("warning", error.message || "Nao foi possivel consultar o CEP.");
      } finally {
        if (label) {
          label.textContent = "CEP";
        }
      }
    },

    async loadCadastroCompleto() {
      if (!this.endpoints.patient) {
        this.showToast("info", "Endpoint de dados do paciente ainda nao configurado.");
        return;
      }

      const codAgenda = this.query("#cod_agenda_status")?.value || "";
      const agendaRow = this.root.querySelector(`tr[data-agenda-id='${codAgenda}']`);
      const codPaciente =
        agendaRow?.dataset.pacienteId ||
        this.query(`#cod_paciente${codAgenda}`)?.value ||
        this.query("#cod_paciente_consulta")?.value ||
        "";
      const loading = this.query("#carregamento_cadcompleto");

      if (!codPaciente) {
        this.showToast("warning", "Nao foi possivel identificar o paciente desta consulta.");
        return;
      }

      this.openModal(this.modalCadCompleto);
      if (loading) {
        loading.classList.remove("hidden");
      }

      try {
        const response = await fetch(this.endpoints.patient, {
          method: "POST",
          headers: {
            "X-CSRFToken": this.csrfToken,
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: new URLSearchParams({
            funcao: "buscar_dados",
            cod_paciente: codPaciente,
          }),
        });

        const data = await response.json();
        if (!response.ok || !data.success) {
          throw new Error(data.message || "Paciente nao encontrado.");
        }

        const paciente = data.paciente || {};
        this.query("#cod_agenda_cadcompleto").value = codAgenda;
        this.query("#cod_paciente").value = paciente.id || "";
        this.query("#cpf").value = paciente.cpf || "";
        this.query("#nome_paciente").value = paciente.nome || "";
        this.query("#celular").value = paciente.celular || "";
        this.query("#telefone").value = paciente.telefone || "";
        this.query("#email").value = paciente.email || "";
        this.query("#documento").value = paciente.documento || "";
        this.query("#nascimento").value = paciente.nascimento || "";
        this.query("#peso").value = paciente.peso || "";
        this.query("#altura").value = paciente.altura || "";
        this.query("#sexo").value = paciente.sexo || "";
        this.query("#profissao").value = paciente.profissao || "";
        this.query("#cep").value = paciente.cep || "";
        this.query("#endereco").value = paciente.endereco || "";
        this.query("#numero").value = paciente.numero || "";
        this.query("#complemento").value = paciente.complemento || "";
        this.query("#bairro").value = paciente.bairro || "";
        this.query("#cidade").value = paciente.cidade || "";
        this.query("#estado").value = paciente.estado || "";
        this.query("#mae").value = paciente.mae || "";
        this.query("#pai").value = paciente.pai || "";
        this.query("#convenio").value = paciente.convenio || "";
        this.query("#num_carteira").value = paciente.num_carteira || "";
        this.query("#carteira_sus").value = paciente.carteira_sus || "";
        this.query("#obs").value = paciente.obs || "";
        this.clearCadastroCompletoValidation();
        this.updateAgeLabel();
      } catch (error) {
        this.showToast("error", error.message || "Nao foi possivel carregar os dados do paciente.");
      } finally {
        if (loading) {
          loading.classList.add("hidden");
        }
      }
    },

    validateCadastroCompleto() {
      const requiredFields = [
        ["#cpf", "Informe o CPF."],
        ["#nome_paciente", "Informe o nome."],
        ["#celular", "Informe o celular."],
        ["#email", "Informe o email."],
        ["#documento", "Informe o documento."],
        ["#nascimento", "Informe a data de nascimento."],
        ["#sexo", "Informe o sexo."],
        ["#profissao", "Informe a profissao."],
        ["#cep", "Informe o CEP."],
        ["#endereco", "Informe o endereco."],
        ["#numero", "Informe o numero."],
        ["#bairro", "Informe o bairro."],
        ["#cidade", "Informe a cidade."],
        ["#estado", "Informe o estado."],
        ["#convenio", "Informe o convenio."],
        ["#num_carteira", "Informe o numero da carteira."],
      ];

      this.clearCadastroCompletoValidation();

      let firstInvalidField = null;

      for (const [selector, message] of requiredFields) {
        const field = this.query(selector);
        if (!field || !field.value || !String(field.value).trim()) {
          this.markFieldInvalid(field, message);
          if (!firstInvalidField) {
            firstInvalidField = field;
          }
        }
      }

      if (firstInvalidField) {
        this.showModalAlert(this.modalCadCompleto, "warning", "Revise os campos obrigatorios destacados.");
        firstInvalidField.focus();
        return false;
      }

      return true;
    },

    async confirmCadastroCompleto(button) {
      if (!this.validateCadastroCompleto()) {
        return;
      }

      if (!this.endpoints.patient) {
        this.showToast("info", "Endpoint de atualizacao do paciente ainda nao configurado.");
        return;
      }

      const payload = {
        funcao: "atualiza_paciente",
        cod_paciente: this.query("#cod_paciente")?.value || "",
        cpf: this.query("#cpf")?.value || "",
        nome: this.query("#nome_paciente")?.value || "",
        celular: this.query("#celular")?.value || "",
        telefone: this.query("#telefone")?.value || "",
        email: this.query("#email")?.value || "",
        documento: this.query("#documento")?.value || "",
        nascimento: this.query("#nascimento")?.value || "",
        peso: this.query("#peso")?.value || "",
        altura: this.query("#altura")?.value || "",
        sexo: this.query("#sexo")?.value || "",
        profissao: this.query("#profissao")?.value || "",
        cep: this.query("#cep")?.value || "",
        endereco: this.query("#endereco")?.value || "",
        numero: this.query("#numero")?.value || "",
        complemento: this.query("#complemento")?.value || "",
        bairro: this.query("#bairro")?.value || "",
        cidade: this.query("#cidade")?.value || "",
        estado: this.query("#estado")?.value || "",
        mae: this.query("#mae")?.value || "",
        pai: this.query("#pai")?.value || "",
        convenio: this.query("#convenio")?.value || "",
        num_carteira: this.query("#num_carteira")?.value || "",
        sus: "N",
        carteira_sus: this.query("#carteira_sus")?.value || "",
        obs: this.query("#obs")?.value || "",
        status: "A",
        cod_agenda: this.query("#cod_agenda_cadcompleto")?.value || "",
      };

      await this.postAction(button, this.endpoints.patient, payload, {
        successMessage: "Cadastro atualizado com sucesso.",
        reloadOnSuccess: true,
        loadingHtml: "<span class='loading loading-spinner loading-xs'></span>",
      });
    },

    prepareNovoHorario(button) {
      this.updateSelectedDoctor();
      if (!this.selectedDoctorId || this.selectedDoctorId === "0") {
        this.showToast("warning", "Selecione um medico antes de adicionar horario.");
        return;
      }

      if (this.query("#cod_medico_addhora")) {
        this.query("#cod_medico_addhora").value = this.selectedDoctorId;
      }
      if (this.query("#nome_medico_addhora")) {
        this.query("#nome_medico_addhora").value = this.selectedDoctorName;
      }

      this.switchModal(button, button.dataset.modalTarget);
    },

    async addHorario(button) {
      if (!this.endpoints.schedule) {
        this.showToast("info", "Endpoint para adicionar horario ainda nao configurado.");
        return;
      }

      const payload = {
        funcao: "addhora",
        data_agenda: this.query("#data_agenda")?.value || "",
        cod_medico: this.query("#cod_medico_addhora")?.value || "",
        hora_agenda: this.query("#nova_hora_addhora")?.value || "",
      };

      await this.postAction(button, this.endpoints.schedule, payload, {
        successMessage: "Horario adicionado com sucesso.",
        reloadOnSuccess: true,
        loadingHtml: "<span class='loading loading-spinner loading-xs'></span>",
      });
    },

    async addAgenda(button) {
      this.updateSelectedDoctor();
      if (!this.selectedDoctorId || this.selectedDoctorId === "0") {
        this.showToast("warning", "Selecione um medico antes de abrir a agenda.");
        return;
      }

      const dataAgenda = this.query("#data_agenda")?.value || "";
      const confirmed = await this.requestConfirmation({
        title: "Abrir agenda",
        message: `Confirma a abertura de uma nova agenda para o dia ${dataAgenda}?`,
        detail: "Os horarios configurados para o medico serao gerados automaticamente nessa data.",
        confirmLabel: "Abrir agenda",
        confirmIcon: "fas fa-calendar-plus",
        confirmButtonClass: "btn-primary",
      });

      if (!confirmed) {
        return;
      }

      if (!this.endpoints.schedule) {
        this.showToast("info", "Endpoint para criar agenda ainda nao configurado.");
        return;
      }

      await this.postAction(button, this.endpoints.schedule, {
        funcao: "criar_agenda",
        data_agenda: dataAgenda,
        cod_medico: this.selectedDoctorId,
      }, {
        successMessage: "Agenda criada com sucesso.",
        reloadOnSuccess: true,
        loadingHtml: "<span class='loading loading-spinner loading-xs'></span>",
      });
    },

    async postAction(button, url, payload, options = {}) {
      const originalHtml = options.restoreHtml || button?.innerHTML || "";
      const shouldDisable = Boolean(button);

      if (button && options.loadingHtml) {
        button.innerHTML = options.loadingHtml;
      }
      if (shouldDisable) {
        button.disabled = true;
      }

      try {
        const response = await fetch(url, {
          method: "POST",
          headers: {
            "X-CSRFToken": this.csrfToken,
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: new URLSearchParams(payload),
        });

        const data = await response.json();
        if (!response.ok || !data.success) {
          throw new Error(data.message || "Falha ao processar a operacao.");
        }

        if (options.successMessage || data.message) {
          this.showToast("success", options.successMessage || data.message);
        }
        if (options.reloadOnSuccess) {
          window.location.reload();
        }
        return data;
      } catch (error) {
        this.showToast("error", error.message || "Falha ao processar a operacao.");
        return null;
      } finally {
        if (button) {
          button.innerHTML = originalHtml;
          button.disabled = false;
        }
      }
    },
  };
};
