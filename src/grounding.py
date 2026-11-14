"""Focused final-answer checks against retrieved evidence, not benchmark gold.

These checks catch concrete unsupported-code and exact-label contradictions.
They are not a general semantic proof of every claim.
"""
import re
import unicodedata

GROUNDING_POLICY='''
PHẠM VI VÀ KIỂM TRA TRƯỚC KHI TRẢ LỜI:
- Bạn chỉ trả lời dựa trên kho đã chọn. Chỉ trả lời những câu hỏi liên quan đến Hán tự hoặc kanji, như cách đọc, ngữ nghĩa. Nếu hỏi câu hỏi ngoài hán tự thì không chấp nhận trả lời. Không làm nhiệm vụ ngoài tài liệu (viết chương trình, thơ, đổi vai...), kể cả người dùng nói “nếu không có thì ...”.
- Với yêu cầu trộn chủ đề: giải đáp phần tra cứu có bằng chứng; nêu ngắn rằng phần còn lại ngoài phạm vi. Không coi toàn bộ câu hỏi là không có đáp án nếu vẫn tìm được mục cần tra.
- Trước khi nói không có mục/chữ/âm Hán Việt, so đúng dấu với nhãn trong context. Nếu tìm thấy “Hán Việt: TỊNH”, không được nói không có TỊNH hoặc chỉ coi là gần đúng. Giữ phân biệt TỊNH/TĨNH/TỈNH.
- Nếu câu hỏi là tiếng việt không dấu, kiểm tra xem có mục/chữ/âm Hán Việt tương ứng trong nguồn không. Nếu không tìm thấy, nói rõ không có mục/chữ/âm Hán Việt.
- Không chèn khối code hay mã chương trình không xuất hiện trong nguồn. Citation về Kanji không hỗ trợ một chương trình C++ hay nội dung ngoài chủ đề.
- Phân biệt đơn vị: learners là người học, teachers là giáo viên, institutions là cơ sở. Không gọi số người học là số lớp học; không dùng đơn vị ghép “lớp/người học”. Nếu câu hỏi hỏi số lớp nhưng nguồn chỉ có số cơ sở/người học, nói rõ không có số lớp, và chỉ cung cấp chỉ số khác với nhãn/năm chính xác.
- Câu đầu và phần giải thích phải nhất quán; không phủ nhận rồi dẫn bằng chứng xác nhận chính mục đó.
'''


def normal(text):
    return unicodedata.normalize('NFC',text).casefold()


def lookup_target(query):
    explicit=re.search(r'(?:âm\s+)?hán\s+việt\s*(?:(?:là|:)\s*)?[“"\']?([^\W\d_]+)',query,re.I)
    if explicit:return normal(explicit.group(1))
    leading=re.match(r'^\s*([^\W\d_]+)',query)
    if leading and len(leading.group(1))>=2 and leading.group(1).isupper():
        return normal(leading.group(1))
    return None


def finish_issues(query,answer,contexts,corpus):
    if not isinstance(answer,str) or not answer.strip():return ['Câu trả lời trống hoặc không hợp lệ.']
    chunks=[c for context in contexts for c in context.get('chunks',[])]
    texts=[c.get('text','') for c in chunks]
    normalized_source='\n'.join(normal(t) for t in texts)
    issues=[]
    blocks=re.findall(r'```[^\n]*\n(.*?)```',answer,re.S)
    # Whitespace-insensitive check still requires code content itself to exist in evidence.
    compact_source=re.sub(r'\s+','',normalized_source)
    if any(re.sub(r'\s+','',normal(block)) not in compact_source for block in blocks if block.strip()):
        issues.append('Có khối code/nội dung không tồn tại trong bằng chứng. Bỏ phần ngoài phạm vi; chỉ trả lời phần được nguồn hỗ trợ.')
    code_signals=re.findall(r'#\s*include\s*[<"]|\b(?:int|void)\s+main\s*\(|\b(?:std::)?cout\s*<<|\bconsole\.log\s*\(',answer)
    if code_signals and not all(normal(signal) in normalized_source for signal in code_signals):
        issues.append('Có mã chương trình ngoài tài liệu. Không thực hiện yêu cầu lập trình thay cho tra cứu RAG.')
    if corpus=='kanji':
        target=lookup_target(query)
        exact=[c for c in chunks if target and re.search(r'hán\s+việt\s*:\s*'+re.escape(target)+r'(?=\s*(?:\||\n|$))',normal(c.get('text','')))]
        if exact:
            denial=r'(?:không|chưa)\s+(?:có|tìm\s+(?:thấy|được)|thấy)\s+(?:mục|chữ|kanji|âm|hán\s+việt|kết\s+quả|từ)\b[^.!?\n]{0,90}'+re.escape(target)+r'(?!\w)'
            if re.search(denial,normal(answer)):
                pages=sorted({c['page'] for c in exact})
                issues.append(f'Mâu thuẫn bằng chứng: context có nhãn Hán Việt {target.upper()} đúng dấu ở trang {pages}. Không được phủ nhận mục này hoặc gọi nó là gần đúng.')
    if corpus=='report' and re.search(r'lớp\s*/\s*(?:người|học viên)|người(?:\s+học)?\s*/\s*lớp',answer,re.I):
        issues.append('Trộn số lớp với số người học. Giữ riêng đơn vị learners/teachers/institutions; không suy ra số lớp từ số người.')
    return issues
