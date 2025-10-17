"""
Backlog API クライアント

requestsライブラリを使用してBacklog API v2を直接呼び出す実装
"""

import logging
from typing import Optional
from datetime import datetime

import requests

from ..models.project import Project, ProjectUser, Status, Priority, Category, Milestone
from ..models.settings import UserInfo
from ..models.task import Task

logger = logging.getLogger(__name__)


class BacklogAPIError(Exception):
    """Backlog API エラー"""

    pass


class BacklogConnectionError(BacklogAPIError):
    """Backlog 接続エラー"""

    pass


class BacklogAuthenticationError(BacklogAPIError):
    """Backlog 認証エラー"""

    pass


class BacklogClient:
    """
    Backlog API クライアント

    Backlog API v2を直接呼び出してアプリケーション固有の機能を提供
    """

    def __init__(
        self,
        space_id: str,
        api_key: str,
        use_https: bool = True,
        timeout: int = 30,
        max_retries: int = 3,
        verify_ssl: bool = True,
        domain: str = "backlog.com",
    ):
        """
        Backlog API クライアントを初期化

        Args:
            space_id: BacklogスペースID
            api_key: Backlog APIキー
            use_https: HTTPS使用（デフォルト: True）
            timeout: タイムアウト秒数（デフォルト: 30）
            max_retries: 最大リトライ回数（デフォルト: 3）
            verify_ssl: SSL証明書を検証（デフォルト: True、企業プロキシ環境ではFalseに）
            domain: Backlogドメイン（デフォルト: backlog.com、日本はbacklog.jp）
        """
        self.space_id = space_id
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl
        self.domain = domain

        protocol = "https" if use_https else "http"
        self.base_url = f"{protocol}://{space_id}.{domain}/api/v2"

        # セッションの作成
        self.session = requests.Session()
        self.session.params = {"apiKey": api_key}  # type: ignore
        self.session.headers.update({"Content-Type": "application/json"})
        self.session.verify = verify_ssl  # SSL検証設定

        if not verify_ssl:
            # SSL警告を抑制
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        logger.info(f"Backlog client initialized: {self.base_url} (SSL verify={verify_ssl})")

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
    ) -> dict | list:
        """
        APIリクエストを実行

        Args:
            method: HTTPメソッド（GET, POST, PUT, DELETE）
            endpoint: APIエンドポイント（/users/myself など）
            params: クエリパラメータ
            json: JSONボディ

        Returns:
            dict | list: APIレスポンス

        Raises:
            BacklogAuthenticationError: 認証エラー
            BacklogConnectionError: 接続エラー
            BacklogAPIError: APIエラー
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                timeout=self.timeout,
            )

            # ステータスコードチェック
            if response.status_code == 401:
                raise BacklogAuthenticationError(
                    f"認証エラー: APIキーが無効です (HTTP {response.status_code})"
                )
            elif response.status_code == 403:
                raise BacklogAuthenticationError(
                    f"権限エラー: アクセス権限がありません (HTTP {response.status_code})"
                )
            elif response.status_code >= 400:
                error_msg = response.text
                raise BacklogAPIError(
                    f"APIエラー (HTTP {response.status_code}): {error_msg}"
                )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            raise BacklogConnectionError(f"タイムアウトエラー: {url}")
        except requests.exceptions.ConnectionError as e:
            raise BacklogConnectionError(f"接続エラー: {e}")
        except BacklogAPIError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in API request: {e}")
            raise BacklogAPIError(f"予期しないエラー: {e}")

    def test_connection(self) -> dict:
        """
        API接続テスト（自分のユーザー情報を取得）

        Returns:
            dict: ユーザー情報の辞書

        Raises:
            BacklogAuthenticationError: 認証エラー
            BacklogConnectionError: 接続エラー
        """
        try:
            logger.debug("Testing Backlog API connection...")
            user_data = self._request("GET", "/users/myself")
            logger.info(f"Connection test successful: {user_data.get('name')}")
            return user_data  # type: ignore

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            raise

    def get_own_user(self) -> UserInfo:
        """
        自分のユーザー情報を取得

        Returns:
            UserInfo: ユーザー情報

        Raises:
            BacklogAPIError: API エラー
        """
        try:
            logger.debug("Fetching own user info...")
            user_data = self._request("GET", "/users/myself")

            user_info = UserInfo(
                id=user_data["id"],  # type: ignore
                user_id=user_data.get("userId", ""),  # type: ignore
                name=user_data.get("name", ""),  # type: ignore
                role_type=user_data.get("roleType", 0),  # type: ignore
                lang=user_data.get("lang"),  # type: ignore
                mail_address=user_data.get("mailAddress"),  # type: ignore
            )

            logger.info(f"Fetched user info: {user_info.name}")
            return user_info

        except Exception as e:
            logger.error(f"Failed to fetch own user info: {e}")
            raise BacklogAPIError(f"ユーザー情報の取得に失敗しました: {e}")

    def get_projects(self, archived: bool = False) -> list[Project]:
        """
        アクセス可能なプロジェクト一覧を取得

        Args:
            archived: アーカイブ済みプロジェクトを含める（デフォルト: False）

        Returns:
            list[Project]: プロジェクトリスト

        Raises:
            BacklogAPIError: API エラー
        """
        try:
            logger.debug(f"Fetching projects (archived={archived})...")
            params = {"archived": str(archived).lower()}
            projects_data = self._request("GET", "/projects", params=params)

            projects = []
            for p in projects_data:  # type: ignore
                project = Project(
                    id=p["id"],
                    project_key=p["projectKey"],
                    name=p["name"],
                    chart_enabled=p.get("chartEnabled", False),
                    subtasking_enabled=p.get("subtaskingEnabled", False),
                    project_leader_can_edit_project_leader=p.get(
                        "projectLeaderCanEditProjectLeader", False
                    ),
                    use_wiki_tree_view=p.get("useWikiTreeView", False),
                    text_formatting_rule=p.get("textFormattingRule", "markdown"),
                    archived=p.get("archived", False),
                )
                projects.append(project)

            logger.info(f"Fetched {len(projects)} projects")
            return projects

        except Exception as e:
            logger.error(f"Failed to fetch projects: {e}")
            raise BacklogAPIError(f"プロジェクト一覧の取得に失敗しました: {e}")

    def get_project(self, project_id_or_key: int | str) -> Project:
        """
        プロジェクト情報を取得

        Args:
            project_id_or_key: プロジェクトIDまたはキー

        Returns:
            Project: プロジェクト情報

        Raises:
            BacklogAPIError: API エラー
        """
        try:
            logger.debug(f"Fetching project: {project_id_or_key}")
            project_data = self._request("GET", f"/projects/{project_id_or_key}")

            project = Project(
                id=project_data["id"],  # type: ignore
                project_key=project_data["projectKey"],  # type: ignore
                name=project_data["name"],  # type: ignore
                chart_enabled=project_data.get("chartEnabled", False),  # type: ignore
                subtasking_enabled=project_data.get("subtaskingEnabled", False),  # type: ignore
                project_leader_can_edit_project_leader=project_data.get(  # type: ignore
                    "projectLeaderCanEditProjectLeader", False
                ),
                use_wiki_tree_view=project_data.get("useWikiTreeView", False),  # type: ignore
                text_formatting_rule=project_data.get("textFormattingRule", "markdown"),  # type: ignore
                archived=project_data.get("archived", False),  # type: ignore
            )

            logger.info(f"Fetched project: {project.name}")
            return project

        except Exception as e:
            logger.error(f"Failed to fetch project {project_id_or_key}: {e}")
            raise BacklogAPIError(f"プロジェクト情報の取得に失敗しました: {e}")

    def get_user_tasks(
        self,
        project_ids: Optional[list[int]] = None,
        status_ids: Optional[list[int]] = None,
        assignee_id: Optional[int] = None,
        assignee_ids: Optional[list[int]] = None,
    ) -> list[Task]:
        """
        タスク（課題）一覧を取得

        Args:
            project_ids: プロジェクトIDリスト（Noneの場合全プロジェクト）
            status_ids: ステータスIDリスト（Noneの場合全ステータス）
            assignee_id: 担当者ID（Noneの場合自分）※非推奨、assignee_idsを使用
            assignee_ids: 担当者IDリスト（複数ユーザーのタスク取得）

        Returns:
            list[Task]: タスクリスト

        Raises:
            BacklogAPIError: API エラー
        """
        try:
            # assignee_idsが指定されていない場合は単一assignee_idを使用
            if assignee_ids is None:
                if assignee_id is None:
                    # どちらも指定されていない場合は自分のIDを取得
                    user_info = self.get_own_user()
                    assignee_ids = [user_info.id]
                else:
                    assignee_ids = [assignee_id]

            logger.debug(
                f"Fetching tasks (projects={project_ids}, "
                f"statuses={status_ids}, assignees={assignee_ids})..."
            )

            # パラメータ構築（Backlog APIは配列を key[]=value1&key[]=value2 形式で受け取る）
            params = {}
            
            # 複数担当者IDを設定
            if assignee_ids:
                params["assigneeId[]"] = assignee_ids  # type: ignore

            if project_ids:
                params["projectId[]"] = project_ids  # type: ignore

            if status_ids:
                params["statusId[]"] = status_ids  # type: ignore

            # タスク取得
            issues_data = self._request("GET", "/issues", params=params)

            tasks = []
            for issue in issues_data:  # type: ignore
                # カテゴリー名リスト
                category_names = (
                    [cat["name"] for cat in issue.get("category", [])]
                    if issue.get("category")
                    else []
                )

                # マイルストーン名リスト
                milestone_names = (
                    [ms["name"] for ms in issue.get("milestone", [])]
                    if issue.get("milestone")
                    else []
                )

                # バージョン名リスト
                version_names = (
                    [v["name"] for v in issue.get("versions", [])]
                    if issue.get("versions")
                    else []
                )

                # カスタム属性の取得
                custom_fields = {}
                for custom_field in issue.get("customFields", []):
                    field_name = custom_field.get("name", "")
                    field_value = custom_field.get("value")
                    
                    # 値が存在する場合のみ追加
                    if field_value is not None:
                        # リスト型の場合（複数選択など）
                        if isinstance(field_value, list):
                            # アイテムに"name"がある場合（選択リスト系）
                            if field_value and isinstance(field_value[0], dict) and "name" in field_value[0]:
                                custom_fields[field_name] = [item["name"] for item in field_value]
                            else:
                                custom_fields[field_name] = field_value
                        # オブジェクト型の場合（単一選択など）
                        elif isinstance(field_value, dict) and "name" in field_value:
                            custom_fields[field_name] = field_value["name"]
                        else:
                            custom_fields[field_name] = field_value

                # 担当者情報
                assignee = issue.get("assignee")
                assignee_id_val = assignee["id"] if assignee else None
                assignee_name_val = assignee["name"] if assignee else None

                # 日付のパース
                def parse_date(date_str: Optional[str]) -> Optional[datetime]:
                    if not date_str:
                        return None
                    try:
                        # Backlog APIは ISO 8601形式で返す
                        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    except Exception:
                        return None

                task = Task(
                    id=issue["id"],
                    key=issue["issueKey"],
                    summary=issue["summary"],
                    description=issue.get("description"),
                    project_id=issue["projectId"],
                    project_key=issue["issueKey"].split("-")[0],
                    project_name="",  # 別途取得が必要な場合はget_projectを呼ぶ
                    status_id=issue["status"]["id"],
                    status_name=issue["status"]["name"],
                    priority_id=issue["priority"]["id"],
                    priority_name=issue["priority"]["name"],
                    assignee_id=assignee_id_val,
                    assignee_name=assignee_name_val,
                    created_user_id=issue["createdUser"]["id"],
                    created_user_name=issue["createdUser"]["name"],
                    due_date=parse_date(issue.get("dueDate")),
                    start_date=parse_date(issue.get("startDate")),
                    created=parse_date(issue.get("created")),
                    updated=parse_date(issue.get("updated")),
                    category_names=category_names,
                    milestone_names=milestone_names,
                    version_names=version_names,
                    estimated_hours=issue.get("estimatedHours"),
                    actual_hours=issue.get("actualHours"),
                    parent_issue_id=issue.get("parentIssueId"),
                    custom_fields=custom_fields,
                )
                tasks.append(task)

            logger.info(f"Fetched {len(tasks)} tasks")
            return tasks

        except Exception as e:
            logger.error(f"Failed to fetch tasks: {e}")
            raise BacklogAPIError(f"タスク一覧の取得に失敗しました: {e}")

    def get_statuses(self, project_id_or_key: int | str) -> list[Status]:
        """
        プロジェクトのステータス一覧を取得

        Args:
            project_id_or_key: プロジェクトIDまたはキー

        Returns:
            list[Status]: ステータスリスト

        Raises:
            BacklogAPIError: API エラー
        """
        try:
            logger.debug(f"Fetching statuses for project: {project_id_or_key}")
            statuses_data = self._request(
                "GET", f"/projects/{project_id_or_key}/statuses"
            )

            statuses = []
            for s in statuses_data:  # type: ignore
                status = Status(
                    id=s["id"],
                    project_id=(
                        project_id_or_key if isinstance(project_id_or_key, int) else 0
                    ),
                    name=s["name"],
                    color=s.get("color", "#000000"),
                    display_order=s.get("displayOrder", 0),
                )
                statuses.append(status)

            logger.info(f"Fetched {len(statuses)} statuses")
            return statuses

        except Exception as e:
            logger.error(f"Failed to fetch statuses: {e}")
            raise BacklogAPIError(f"ステータス一覧の取得に失敗しました: {e}")

    def get_project_users(self, project_id_or_key: int | str) -> list[ProjectUser]:
        """
        プロジェクトのユーザー（メンバー）一覧を取得

        Args:
            project_id_or_key: プロジェクトIDまたはキー

        Returns:
            list[ProjectUser]: プロジェクトユーザーリスト

        Raises:
            BacklogAPIError: API エラー
        """
        try:
            logger.debug(f"Fetching users for project: {project_id_or_key}")
            users_data = self._request(
                "GET", f"/projects/{project_id_or_key}/users"
            )

            users = []
            for u in users_data:  # type: ignore
                user = ProjectUser(
                    id=u["id"],
                    user_id=u["userId"],
                    name=u["name"],
                    role_type=u.get("roleType", 1),
                    lang=u.get("lang"),
                    mail_address=u.get("mailAddress"),
                )
                users.append(user)

            logger.info(f"Fetched {len(users)} users for project {project_id_or_key}")
            return users

        except Exception as e:
            logger.error(f"Failed to fetch project users: {e}")
            raise BacklogAPIError(f"プロジェクトユーザー一覧の取得に失敗しました: {e}")

    def close(self):
        """セッションをクローズ"""
        if self.session:
            self.session.close()
            logger.debug("Backlog client session closed")

    def __enter__(self):
        """コンテキストマネージャー: with文のサポート"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー: 終了時にセッションをクローズ"""
        self.close()

    def __repr__(self) -> str:
        """開発者向け文字列表現"""
        return f"BacklogClient(space='{self.space_id}', base_url='{self.base_url}')"
