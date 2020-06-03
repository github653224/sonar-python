from typing import Any, Optional

class LDAPObject:
    def simple_bind(self, who: Optional[Any], cred: Optional[Any], serverctrls: Optional[Any], clientctrls: Optional[Any]) -> int: ...
    def simple_bind_s(self, who: Optional[Any], cred: Optional[Any], serverctrls: Optional[Any], clientctrls: Optional[Any]) -> None: ...
    def bind(self, who: Any, cred: Any, method: Any) -> int:...
    def bind_s(self, who: Any, cred: Any, method: Any) -> None:...
