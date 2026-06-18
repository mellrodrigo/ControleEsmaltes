# Integração com o site (NGHair-landigpage)

Objetivo: adicionar no menu **"Empresas"** do site um link **"Administração"**
que abre o app de Controle de Esmaltes.

> Esta sessão tem acesso só ao repositório `ControleEsmaltes`. A edição do
> menu deve ser feita na **outra sessão**, apontando para o repositório
> `mellrodrigo/NGHair-landigpage`. Use as instruções abaixo lá.

## 1. Endereço do app

O app roda no seu servidor (deploy automático a partir deste repositório).
Defina o endereço público dele — recomendado um **subdomínio**, por exemplo:

```
https://esmaltes.SEU-DOMINIO.com.br
```

(Use subdomínio em vez de subpasta para não precisar reescrever os caminhos
dos arquivos estáticos do app.)

## 2. Trecho do link para o menu "Empresas"

Adicione este item dentro da lista do menu **Empresas** do site:

```html
<a href="https://esmaltes.SEU-DOMINIO.com.br" target="_blank" rel="noopener">
  Administração
</a>
```

Se o menu usa `<li>` (padrão de navbar):

```html
<li class="nav-item">
  <a class="nav-link" href="https://esmaltes.SEU-DOMINIO.com.br"
     target="_blank" rel="noopener">Administração</a>
</li>
```

Troque `https://esmaltes.SEU-DOMINIO.com.br` pelo endereço real do app.

## 3. Prompt para a outra sessão

Cole isto na sessão do Claude Code aberta no repositório `NGHair-landigpage`:

> No menu "Empresas" do site, adicione um novo item de link chamado
> "Administração" que aponta para `https://esmaltes.SEU-DOMINIO.com.br`
> (abrir em nova aba). Mantenha o mesmo estilo/classes dos outros itens do
> menu. Faça o commit e o push.

## 4. Proteção do painel (recomendado)

O painel "Administração" fica acessível pela internet. Para exigir senha,
defina no servidor as variáveis de ambiente:

```
ADMIN_USER=seu_usuario
ADMIN_PASS=sua_senha_forte
```

Sem essas variáveis o painel fica aberto (útil só para teste local).
