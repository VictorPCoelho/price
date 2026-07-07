// Cronômetro da página "Estudar agora": alimenta o campo de minutos da sessão.
(function () {
  var mostrador = document.getElementById("mostrador");
  if (!mostrador) return;

  var botaoIniciar = document.getElementById("botao-iniciar");
  var botaoZerar = document.getElementById("botao-zerar");
  var campoMinutos = document.getElementById("campo-minutos");

  var segundos = 0;
  var intervalo = null;

  function desenhar() {
    var m = Math.floor(segundos / 60);
    var s = segundos % 60;
    mostrador.textContent =
      String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
    if (segundos > 0 && campoMinutos) {
      campoMinutos.value = Math.max(1, Math.round(segundos / 60));
    }
  }

  botaoIniciar.addEventListener("click", function () {
    if (intervalo) {
      clearInterval(intervalo);
      intervalo = null;
      botaoIniciar.textContent = "▶ Retomar";
    } else {
      intervalo = setInterval(function () {
        segundos += 1;
        desenhar();
      }, 1000);
      botaoIniciar.textContent = "⏸ Pausar";
    }
  });

  botaoZerar.addEventListener("click", function () {
    clearInterval(intervalo);
    intervalo = null;
    segundos = 0;
    botaoIniciar.textContent = "▶ Iniciar";
    desenhar();
  });

  // aviso ao sair com o cronômetro rodando (evita perder tempo medido),
  // exceto quando a saída é o próprio envio da sessão
  var enviando = false;
  var formulario = document.querySelector('form[action="/sessoes"]');
  if (formulario) {
    formulario.addEventListener("submit", function () {
      enviando = true;
    });
  }
  window.addEventListener("beforeunload", function (evento) {
    if (!enviando && intervalo && segundos > 30) {
      evento.preventDefault();
      evento.returnValue = "";
    }
  });
})();
