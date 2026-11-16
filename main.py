"""Python·Git 학습용 콘솔 퀴즈 게임 (Python 3.10+)."""

import json
from pathlib import Path


# main.py가 들어 있는 폴더에 저장합니다.
STATE_FILE = Path(__file__).resolve().parent / "state.json"


class Quiz:
    """문제 하나를 표현하는 클래스."""

    def __init__(self, question: str, choices: list[str], answer: int):
        if not isinstance(question, str) or not question.strip():
            raise ValueError("문제는 빈 문자열일 수 없습니다.")
        if (not isinstance(choices, list) or len(choices) != 4
                or any(not isinstance(c, str) or not c.strip() for c in choices)):
            raise ValueError("선택지는 내용이 있는 문자열 4개여야 합니다.")
        if type(answer) is not int or answer not in range(1, 5):
            raise ValueError("정답은 1~4 사이의 정수여야 합니다.")
        self.question = question.strip()
        self.choices = [choice.strip() for choice in choices]
        self.answer = answer

    def show(self) -> None:
        print(f"\n{self.question}")
        for number, choice in enumerate(self.choices, start=1):
            print(f"  {number}. {choice}")

    def is_correct(self, number: int) -> bool:
        return number == self.answer

    def to_dict(self) -> dict:
        return {"question": self.question, "choices": self.choices, "answer": self.answer}

    @classmethod
    def from_dict(cls, data: dict) -> "Quiz":
        if not isinstance(data, dict):
            raise ValueError("퀴즈 데이터는 객체여야 합니다.")
        return cls(data["question"], data["choices"], data["answer"])


def default_quizzes() -> list[Quiz]:
    """state.json이 없거나 손상되었을 때 쓸 기본 문제 5개."""
    return [
        Quiz("Python에서 목록을 표현하는 자료형은?",
             ["int", "list", "bool", "str"], 2),
        Quiz("Python에서 조건문을 시작할 때 사용하는 키워드는?",
             ["for", "def", "if", "class"], 3),
        Quiz("함수 정의에 사용하는 키워드는?",
             ["return", "def", "while", "import"], 2),
        Quiz("Git에서 변경사항을 커밋할 대상으로 올리는 명령어는?",
             ["git add", "git pull", "git clone", "git status"], 1),
        Quiz("원격 저장소를 내 컴퓨터에 복제하는 명령어는?",
             ["git merge", "git push", "git clone", "git init"], 3),
    ]


class QuizGame:
    """메뉴, 퀴즈 진행, 최고 점수, JSON 저장을 관리하는 클래스."""

    def __init__(self):
        self.quizzes: list[Quiz] = []
        self.best_score: int | None = None
        self.load_state()

    def save_state(self) -> None:
        """UTF-8 JSON 파일로 저장. 임시 파일에 쓴 후 교체합니다."""
        data = {
            "quizzes": [quiz.to_dict() for quiz in self.quizzes],
            "best_score": self.best_score,
        }
        temporary = STATE_FILE.with_suffix(".json.tmp")
        try:
            with temporary.open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            temporary.replace(STATE_FILE)
        except OSError as error:
            print(f"[저장 오류] 파일을 저장하지 못했습니다: {error}")
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

    def load_state(self) -> None:
        """파일이 없거나 깨졌으면 기본 퀴즈로 시작합니다."""
        if not STATE_FILE.exists():
            print("저장 파일이 없어 기본 퀴즈 5개로 시작합니다.")
            self.quizzes = default_quizzes()
            self.best_score = None
            self.save_state()
            return

        try:
            with STATE_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if not isinstance(data, dict):
                raise ValueError("최상위 데이터가 객체가 아닙니다.")
            raw_quizzes = data["quizzes"]
            best_score = data["best_score"]
            if not isinstance(raw_quizzes, list):
                raise ValueError("quizzes는 목록이어야 합니다.")
            if best_score is not None and (type(best_score) is not int or best_score < 0):
                raise ValueError("best_score 값이 잘못되었습니다.")
            quizzes = [Quiz.from_dict(item) for item in raw_quizzes]
            self.quizzes = quizzes
            self.best_score = best_score
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError, KeyError, TypeError) as error:
            print(f"[불러오기 오류] 파일을 읽을 수 없습니다: {error}")
            print("기본 퀴즈 5개로 복구합니다. 기존 데이터는 별도 백업되지 않습니다.")
            self.quizzes = default_quizzes()
            self.best_score = None
            self.save_state()

    @staticmethod
    def ask_number(prompt: str, minimum: int, maximum: int) -> int:
        """공백, 빈 입력, 문자 입력, 범위 밖 숫자를 처리합니다."""
        while True:
            value = input(prompt).strip()
            if not value:
                print("빈 입력입니다. 숫자를 입력하세요.")
                continue
            try:
                number = int(value)
            except ValueError:
                print("숫자만 입력하세요.")
                continue
            if not minimum <= number <= maximum:
                print(f"{minimum}~{maximum} 사이의 번호를 입력하세요.")
                continue
            return number

    @staticmethod
    def ask_text(prompt: str) -> str:
        while True:
            value = input(prompt).strip()
            if value:
                return value
            print("내용을 비워둘 수 없습니다. 다시 입력하세요.")

    def play(self) -> None:
        if not self.quizzes:
            print("등록된 퀴즈가 없습니다. 먼저 퀴즈를 추가하세요.")
            return
        
        score = 0
        total = len(self.quizzes)

        print(f"\n총 {total}개의 문제가 준비되어 있습니다.")

        for index, quiz in enumerate(self.quizzes, start=1):
            print(f"\n--- 문제 {index}/{total} ---")
            quiz.show()
            answer = self.ask_number("정답 번호 (1~4): ", 1, 4)
            if quiz.is_correct(answer):
                score += 1
                print("정답입니다!")
            else:
                print(f"오답입니다. 정답은 {quiz.answer}번입니다.")

        print(f"\n게임 종료! {total}문제 중 {score}문제를 맞혔습니다.")
        if self.best_score is None or score > self.best_score:
            self.best_score = score
            print("새로운 최고 점수입니다!")
        else:
            print(f"현재 최고 점수: {self.best_score}점")
        self.save_state()

    def add_quiz(self) -> None:
        print("\n--- 퀴즈 추가 ---")
        question = self.ask_text("문제: ")
        choices = [self.ask_text(f"선택지 {number}: ") for number in range(1, 5)]
        answer = self.ask_number("정답 번호 (1~4): ", 1, 4)
        self.quizzes.append(Quiz(question, choices, answer))
        self.save_state()
        print("퀴즈가 추가되었습니다.")

    def show_quizzes(self) -> None:
        if not self.quizzes:
            print("등록된 퀴즈가 없습니다.")
            return
        print(f"\n--- 퀴즈 목록 (총 {len(self.quizzes)}개) ---")
        for index, quiz in enumerate(self.quizzes, start=1):
            print(f"\n[{index}번 문제]")
            quiz.show()
            print(f"  정답: {quiz.answer}번")

    def show_best_score(self) -> None:
        if self.best_score is None:
            print("아직 퀴즈를 푼 기록이 없습니다.")
        else:
            print(f"최고 점수: {self.best_score}점")

    def run(self) -> None:
        try:
            while True:
                print("\n===== Python·Git 퀴즈 게임 =====")
                print("1. 퀴즈 풀기")
                print("2. 퀴즈 추가")
                print("3. 퀴즈 목록")
                print("4. 최고 점수 확인")
                print("5. 종료")
                menu = self.ask_number("메뉴 선택 (1~5): ", 1, 5)
                if menu == 1:
                    self.play()
                elif menu == 2:
                    self.add_quiz()
                elif menu == 3:
                    self.show_quizzes()
                elif menu == 4:
                    self.show_best_score()
                else:
                    print("게임을 종료합니다.")
                    break
        except (KeyboardInterrupt, EOFError):
            print("\n입력이 중단되었습니다. 데이터를 저장하고 안전하게 종료합니다.")
        finally:
            self.save_state()


if __name__ == "__main__":
    QuizGame().run()
