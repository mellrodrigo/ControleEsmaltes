# Integração com o site (NGHair-landigpage)

Objetivo: o item **"Administração"** do menu **"Empresas"** do site deve abrir
o app de Controle de Esmaltes.

> Esta sessão tem acesso só ao repositório `ControleEsmaltes`. A edição do
> menu deve ser feita na **outra sessão**, apontando para o repositório
> `mellrodrigo/NGHair-landigpage`. Use as instruções abaixo lá.

## Endereço do app

O app roda no subdomínio (veja `DEPLOY-VPS.md` para publicá-lo):

```
https://esmaltes.nghair.com.br
```

> ⚠️ O link **não** pode apontar para um caminho dentro do site estático
> (ex.: `https://www.nghair.com.br/controleEsmaltes`) — isso dá **404**, pois
> a landing page não tem essa rota e o app Python roda em outro endereço.

## Correção do link (o que está errado hoje)

Hoje o item "Administração" aponta para um subcaminho do site, que dá 404.
Troque o `href` (no menu **desktop e no mobile**):

```diff
- href="https://www.nghair.com.br/controleEsmaltes"
+ href="https://esmaltes.nghair.com.br"
```

## Prompt para a outra sessão (repositório do site)

Cole isto na sessão do Claude Code aberta no repositório `NGHair-landigpage`:

> No menu "Empresas" do site existe um item "Administração" cujo link aponta
> para `https://www.nghair.com.br/controleEsmaltes` e está dando erro 404.
> Corrija o `href` desse item para `https://esmaltes.nghair.com.br`, mantendo
> `target="_blank"` e `rel="noopener noreferrer"`. O link aparece tanto no
> menu desktop quanto no mobile — ajuste nos dois lugares. Não altere mais
> nada. Mostre o diff, faça commit e push e abra um Pull Request em rascunho.

## Proteção do painel (recomendado)

O painel "Administração" fica acessível pela internet. Para exigir senha,
defina no servidor as variáveis de ambiente:

```
ADMIN_USER=seu_usuario
ADMIN_PASS=sua_senha_forte
```

Sem essas variáveis o painel fica aberto (útil só para teste local).
