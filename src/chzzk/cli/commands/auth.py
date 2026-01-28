"""Authentication commands for CLI."""

from __future__ import annotations

import asyncio
import json
import re
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Annotated

import httpx
import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

if TYPE_CHECKING:
    from chzzk.cli.config import ConfigManager

app = typer.Typer(no_args_is_help=True)
console = Console()

# Naver login endpoints
NAVER_NID_BASE = "https://nid.naver.com"
NAVER_QR_LOGIN_URL = f"{NAVER_NID_BASE}/nidlogin.login"
NAVER_SCHEME_CHECK_URL = f"{NAVER_NID_BASE}/login/scheme.check"


def get_config(ctx: typer.Context) -> ConfigManager:
    """Get ConfigManager from context."""
    return ctx.obj["config"]


def _prompt_login_fallback(config: ConfigManager) -> tuple[str, str]:
    """Fallback prompt-based login for non-TTY environments.

    Args:
        config: Configuration manager.

    Returns:
        Tuple of (nid_aut, nid_ses) values.
    """
    nid_aut = typer.prompt("NID_AUT cookie value")
    nid_ses = typer.prompt("NID_SES cookie value")
    return nid_aut, nid_ses


@app.command()
def login(
    ctx: typer.Context,
    nid_aut: Annotated[
        str | None,
        typer.Option(
            "--nid-aut",
            help="NID_AUT cookie value from Naver login",
        ),
    ] = None,
    nid_ses: Annotated[
        str | None,
        typer.Option(
            "--nid-ses",
            help="NID_SES cookie value from Naver login",
        ),
    ] = None,
) -> None:
    """Save Naver authentication cookies.

    You can get these cookies from your browser after logging into Naver:
    1. Open browser DevTools (F12)
    2. Go to Application > Cookies > naver.com
    3. Find NID_AUT and NID_SES values
    """
    config = get_config(ctx)
    json_output = ctx.obj.get("json_output", False)

    # If both values provided via CLI, skip prompts
    if nid_aut and nid_ses:
        config.save_cookies(nid_aut, nid_ses)
        if json_output:
            console.print(json.dumps({"status": "success", "message": "Cookies saved"}))
        else:
            console.print(
                Panel(
                    f"Cookies saved to [cyan]{config.config_dir}[/cyan]",
                    title="[green]Login successful[/green]",
                    border_style="green",
                )
            )
        return

    # Use simple prompts
    try:
        final_nid_aut, final_nid_ses = _prompt_login_fallback(config)
    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]Login cancelled[/yellow]")
        raise typer.Exit(0) from None

    config.save_cookies(final_nid_aut, final_nid_ses)

    if json_output:
        console.print(json.dumps({"status": "success", "message": "Cookies saved"}))
    else:
        console.print(
            Panel(
                f"Cookies saved to [cyan]{config.config_dir}[/cyan]",
                title="[green]Login successful[/green]",
                border_style="green",
            )
        )


@app.command()
def status(ctx: typer.Context) -> None:
    """Check authentication status."""
    config = get_config(ctx)
    nid_aut, nid_ses = config.get_auth_cookies(
        cli_nid_aut=ctx.obj.get("nid_aut"),
        cli_nid_ses=ctx.obj.get("nid_ses"),
    )

    has_auth = bool(nid_aut and nid_ses)

    if ctx.obj.get("json_output"):
        result = {
            "authenticated": has_auth,
            "has_nid_aut": bool(nid_aut),
            "has_nid_ses": bool(nid_ses),
            "has_stored_cookies": config.has_stored_cookies(),
        }
        console.print(json.dumps(result))
    else:
        if has_auth:
            # Mask cookie values for display
            aut_masked = nid_aut[:8] + "..." if nid_aut and len(nid_aut) > 8 else nid_aut
            ses_masked = nid_ses[:8] + "..." if nid_ses and len(nid_ses) > 8 else nid_ses

            console.print(
                Panel(
                    f"[green]Authenticated[/green]\n\n"
                    f"NID_AUT: [dim]{aut_masked}[/dim]\n"
                    f"NID_SES: [dim]{ses_masked}[/dim]\n\n"
                    f"Stored cookies: {'Yes' if config.has_stored_cookies() else 'No'}",
                    title="Authentication Status",
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel(
                    "[red]Not authenticated[/red]\n\n"
                    "Run [cyan]chzzk auth login[/cyan] to save your cookies.",
                    title="Authentication Status",
                    border_style="red",
                )
            )


@app.command()
def qr(
    ctx: typer.Context,
    timeout: Annotated[
        int,
        typer.Option(
            "--timeout",
            "-t",
            help="Login wait timeout in seconds",
        ),
    ] = 180,
) -> None:
    """Login via Naver QR code.

    Displays a QR code in the terminal. Scan it with the Naver app
    and select the verification number to complete login.
    """
    asyncio.run(_qr_login(ctx, timeout))


async def _get_qr_session(client: httpx.AsyncClient) -> dict:
    """Get QR code session from Naver login page.

    Args:
        client: HTTP client with cookies.

    Returns:
        Dictionary containing:
        - session: QR code session key
        - secure_value: 2-digit verification number
        - qr_image_base64: Base64 encoded QR image

    Raises:
        ValueError: If QR session cannot be extracted (network blocked, etc.)
    """
    # First visit main login page to get initial cookies
    await client.get(NAVER_QR_LOGIN_URL)

    # Then request QR mode with full parameters (like browser does)
    resp = await client.get(
        NAVER_QR_LOGIN_URL,
        params={
            "mode": "qrcode",
            "url": "https://www.naver.com/",
            "locale": "en_US",
            "svctype": "1",
        },
        headers={"Referer": NAVER_QR_LOGIN_URL},
        follow_redirects=True,
    )
    resp.raise_for_status()

    html = resp.text

    # Check for network block message
    if "네트워크 환경이 불안정합니다" in html or ("warning" in html and "warning_title" in html):
        raise ValueError(
            "네이버가 현재 네트워크 접근을 차단했습니다. "
            "한국 네트워크에서 다시 시도하거나, VPN을 사용해주세요."
        )

    # Extract qrcodesession - try multiple patterns
    session = None
    session_patterns = [
        r'id="qrcodesession"[^>]*value="([^"]+)"',
        r'name="qrcodesession"[^>]*value="([^"]+)"',
        r'value="([^"]+)"[^>]*name="qrcodesession"',
        r'value="([^"]+)"[^>]*id="qrcodesession"',
    ]
    for pattern in session_patterns:
        match = re.search(pattern, html)
        if match:
            session = match.group(1)
            break

    if not session:
        raise ValueError(
            "QR 세션을 찾을 수 없습니다. 네이버 로그인 페이지 구조가 변경되었을 수 있습니다."
        )

    # Extract secureValue (2-digit verification number)
    # Format varies by locale:
    # - Korean: <strong class="point">52</strong>
    # - English: <strong class="point" id="secureValue">27</strong>
    secure_value = None
    secure_patterns = [
        r'<strong[^>]*class="point"[^>]*>(\d+)</strong>',
        r'id="secureValue"[^>]*>(\d+)<',
    ]
    for pattern in secure_patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            secure_value = match.group(1)
            break

    if not secure_value:
        raise ValueError("확인 숫자를 찾을 수 없습니다.")

    # Extract QR code Base64 image
    # Format: <img src="data:image/jpeg;base64, ..." class="qr_img">
    qr_image_base64 = None
    qr_image_patterns = [
        r'<img[^>]*src="(data:image/[^;]+;base64,\s*[^"]+)"[^>]*class="qr_img"',
        r'<img[^>]*class="qr_img"[^>]*src="(data:image/[^;]+;base64,\s*[^"]+)"',
        r'id="qrImage"[^>]*src="(data:image/[^;]+;base64,\s*[^"]+)"',
        r'src="(data:image/[^;]+;base64,\s*[^"]+)"[^>]*id="qrImage"',
    ]
    for pattern in qr_image_patterns:
        match = re.search(pattern, html)
        if match:
            qr_image_base64 = match.group(1)
            break

    if not qr_image_base64:
        raise ValueError("QR 이미지를 찾을 수 없습니다.")

    return {
        "session": session,
        "secure_value": secure_value,
        "qr_image_base64": qr_image_base64,
    }


def _generate_qr_ascii(session: str) -> str:
    """Generate ASCII QR code using qrcode library.

    Args:
        session: QR code session key.

    Returns:
        ASCII representation of QR code.
    """
    import io

    import qrcode  # type: ignore[import-untyped]

    qr_url = f"https://nid.naver.com/nidlogin.qrcode?mode=qrcode&qrcodesession={session}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=1,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)

    output = io.StringIO()
    qr.print_ascii(out=output, invert=True)
    return output.getvalue()


async def _poll_login_status(
    client: httpx.AsyncClient,
    session: str,
    timeout: int,
    on_update: Callable[[int], None],
) -> bool:
    """Poll for login completion.

    Args:
        client: HTTP client with cookies.
        session: QR code session key.
        timeout: Maximum wait time in seconds.
        on_update: Callback with remaining time.

    Returns:
        True if login succeeded, False if timed out.
    """
    start = time.time()
    poll_interval = 2

    while True:
        elapsed = time.time() - start
        remaining = timeout - elapsed

        if remaining <= 0:
            return False

        on_update(int(remaining))

        try:
            resp = await client.get(
                NAVER_SCHEME_CHECK_URL,
                params={"session": session, "cnt": "once"},
            )

            # Check various success indicators
            if resp.status_code == 200:
                text = resp.text
                # Success when response indicates login complete
                # API returns {"auth_result":"success"} on successful scan
                if '"auth_result":"success"' in text:
                    return True
        except httpx.RequestError:
            pass  # Continue polling on network errors

        await asyncio.sleep(poll_interval)


async def _complete_login(client: httpx.AsyncClient, session: str) -> dict[str, str]:
    """Complete login and extract cookies.

    Args:
        client: HTTP client with cookies.
        session: QR code session key.

    Returns:
        Dictionary with NID_AUT and NID_SES cookies.
    """
    resp = await client.post(
        NAVER_QR_LOGIN_URL,
        data={
            "mode": "qrcode",
            "qrcodesession": session,
            "next_step": "false",
        },
        follow_redirects=True,
    )

    # Extract cookies from response and client jar
    nid_aut = None
    nid_ses = None

    # Check response cookies
    for cookie in resp.cookies.jar:
        if cookie.name == "NID_AUT":
            nid_aut = cookie.value
        elif cookie.name == "NID_SES":
            nid_ses = cookie.value

    # Also check client cookie jar
    for cookie in client.cookies.jar:
        if cookie.name == "NID_AUT" and not nid_aut:
            nid_aut = cookie.value
        elif cookie.name == "NID_SES" and not nid_ses:
            nid_ses = cookie.value

    if not nid_aut or not nid_ses:
        raise ValueError(
            f"Failed to extract cookies. Got NID_AUT={bool(nid_aut)}, NID_SES={bool(nid_ses)}"
        )

    return {"NID_AUT": nid_aut, "NID_SES": nid_ses}


async def _qr_login(ctx: typer.Context, timeout: int) -> None:
    """Perform QR code login flow.

    Args:
        ctx: Typer context.
        timeout: Maximum wait time in seconds.
    """
    config = get_config(ctx)
    json_output = ctx.obj.get("json_output", False)

    if not json_output:
        console.print("\n[bold]네이버 QR 코드 로그인[/bold]")
        console.print("━" * 30 + "\n")

    try:
        async with httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
            },
            follow_redirects=True,
        ) as client:
            # Step 1: Get QR session
            if not json_output:
                console.print("[dim]QR 코드 세션 생성 중...[/dim]")

            try:
                qr_data = await _get_qr_session(client)
            except ValueError as e:
                if json_output:
                    console.print(json.dumps({"status": "error", "message": str(e)}))
                else:
                    console.print(f"[red]오류: {e}[/red]")
                raise typer.Exit(1) from None

            # Step 2: Display QR code
            qr_ascii = _generate_qr_ascii(qr_data["session"])

            if json_output:
                console.print(
                    json.dumps(
                        {
                            "status": "waiting",
                            "qr_image_base64": qr_data["qr_image_base64"],
                            "secure_value": qr_data["secure_value"],
                            "message": "Scan QR code with Naver app",
                        }
                    )
                )
            else:
                console.print(qr_ascii)
                console.print(f"\n[bold yellow]확인 숫자: {qr_data['secure_value']}[/bold yellow]")
                console.print("\n네이버 앱으로 QR 코드를 스캔한 후")
                console.print("위 숫자를 선택하세요.\n")

            # Step 3: Poll for login completion
            remaining_time = [timeout]

            def update_remaining(t: int) -> None:
                remaining_time[0] = t

            if not json_output:
                with Live(console=console, refresh_per_second=1) as live:

                    async def poll_with_display() -> bool:
                        start = time.time()
                        poll_interval = 2

                        while True:
                            elapsed = time.time() - start
                            remaining = timeout - elapsed

                            if remaining <= 0:
                                return False

                            minutes = int(remaining) // 60
                            seconds = int(remaining) % 60
                            live.update(
                                Text(f"대기 중... ({minutes:02d}:{seconds:02d} 남음)", style="dim")
                            )

                            try:
                                resp = await client.get(
                                    NAVER_SCHEME_CHECK_URL,
                                    params={"session": qr_data["session"], "cnt": "once"},
                                )

                                if resp.status_code == 200:
                                    text = resp.text
                                    # API returns {"auth_result":"success"} on successful scan
                                    if '"auth_result":"success"' in text:
                                        return True
                            except httpx.RequestError:
                                pass

                            await asyncio.sleep(poll_interval)

                    login_success = await poll_with_display()
            else:
                login_success = await _poll_login_status(
                    client, qr_data["session"], timeout, update_remaining
                )

            if not login_success:
                if json_output:
                    console.print(
                        json.dumps({"status": "error", "message": "Login timeout"})
                    )
                else:
                    console.print("\n[red]타임아웃: 로그인 시간이 초과되었습니다.[/red]")
                    console.print("[dim]다시 시도하려면 chzzk auth qr를 실행하세요.[/dim]")
                raise typer.Exit(1)

            # Step 4: Complete login and extract cookies
            try:
                cookies = await _complete_login(client, qr_data["session"])
            except ValueError as e:
                if json_output:
                    console.print(json.dumps({"status": "error", "message": str(e)}))
                else:
                    console.print(f"\n[red]쿠키 추출 실패: {e}[/red]")
                raise typer.Exit(1) from None

            # Step 5: Save cookies
            config.save_cookies(cookies["NID_AUT"], cookies["NID_SES"])

            if json_output:
                console.print(
                    json.dumps(
                        {
                            "status": "success",
                            "message": "Login successful",
                            "cookies_saved": str(config.config_dir / "cookies.json"),
                        }
                    )
                )
            else:
                console.print("\n[green]✓ 로그인 성공![/green]")
                console.print(
                    f"  쿠키 저장 완료: [cyan]{config.config_dir / 'cookies.json'}[/cyan]"
                )

    except httpx.RequestError as e:
        if json_output:
            console.print(json.dumps({"status": "error", "message": f"Network error: {e}"}))
        else:
            console.print(f"[red]네트워크 오류: {e}[/red]")
        raise typer.Exit(1) from None


@app.command()
def logout(ctx: typer.Context) -> None:
    """Delete stored authentication cookies."""
    config = get_config(ctx)

    if not config.has_stored_cookies():
        if ctx.obj.get("json_output"):
            console.print(json.dumps({"status": "info", "message": "No cookies stored"}))
        else:
            console.print("[yellow]No stored cookies to delete.[/yellow]")
        return

    config.delete_cookies()

    if ctx.obj.get("json_output"):
        console.print(json.dumps({"status": "success", "message": "Cookies deleted"}))
    else:
        console.print(
            Panel(
                "Stored cookies have been deleted.",
                title="[green]Logout successful[/green]",
                border_style="green",
            )
        )
