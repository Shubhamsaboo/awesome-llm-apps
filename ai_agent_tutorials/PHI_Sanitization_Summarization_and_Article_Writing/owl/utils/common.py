# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========
import sys

sys.path.append("../")

import re
from typing import Optional
from camel.logger import get_logger

logger = get_logger(__name__)


def extract_pattern(content: str, pattern: str) -> Optional[str]:
    try:
        _pattern = rf"<{pattern}>(.*?)</{pattern}>"
        match = re.search(_pattern, content, re.DOTALL)
        if match:
            text = match.group(1)
            return text.strip()
        else:
            return None
    except Exception as e:
        logger.warning(f"Error extracting answer: {e}, current content: {content}")
        return None
