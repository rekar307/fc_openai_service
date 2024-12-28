import os
import cv2
import streamlit as st
from openai import OpenAI
from github import Github
from dotenv import load_dotenv
from PIL import Image

# .env 파일 로드
load_dotenv()

# OpenAI API 클라이언트 초기화
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# GitHub API 클라이언트 초기화
github_token = os.getenv("GITHUB_TOKEN")
github_repo = os.getenv("GITHUB_REPO")
g = Github(github_token)
repo = g.get_repo(github_repo)


def describe(image_url):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "이 이미지에 대해서 설명해줘.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url},
                    },
                ],
            },
        ],
        max_tokens=1024,
    )
    return response.choices[0].message.content


def upload_to_github(file_path, repo, commit_message="Add captured image"):
    with open(file_path, "rb") as file:
        content = file.read()
    try:
        # 파일이 이미 존재하는지 확인
        contents = repo.get_contents(file_path)
        repo.update_file(contents.path, commit_message, content, contents.sha)
    except:
        repo.create_file(file_path, commit_message, content)
    # 원시 URL 반환
    return f"https://raw.githubusercontent.com/{repo.full_name}/main/{file_path}"


st.title("진수의 AI 도슨트\n이미지를 설명해드려요!")

# 수평 막대 생성
col1, col2 = st.columns(2)

with col1:
    st.header("이미지 주소 입력")
    input_url = st.text_area("여기에 이미지 주소를 입력하세요")

    if st.button("이미지 주소 해설"):
        if input_url:
            try:
                st.session_state["input_url"] = input_url
                st.session_state["result_url"] = describe(input_url)
            except Exception as e:
                st.error(f"요청 오류가 발생했습니다: {e}")
        else:
            st.warning("이미지 주소를 입력하세요!")

    if "input_url" in st.session_state:
        st.image(st.session_state["input_url"], width=300, caption="입력된 이미지 주소")
    if "result_url" in st.session_state:
        st.success(st.session_state["result_url"])

with col2:
    st.header("이미지 파일 업로드")
    uploaded_file = st.file_uploader(
        "이미지 파일을 업로드하세요", type=["jpg", "jpeg", "png"]
    )

    if st.button("파일 업로드 해설"):
        if uploaded_file is not None:
            # 업로드된 파일을 저장
            img_path = f"uploaded_{uploaded_file.name}"
            with open(img_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # 이미지를 화면에 표시
            st.session_state["img_path"] = img_path

            # 이미지 형식 확인
            try:
                img = Image.open(img_path)
                img_format = img.format.lower()
                if img_format not in ["png", "jpeg", "gif", "webp"]:
                    st.error(
                        "지원되지 않는 이미지 형식입니다. png, jpeg, gif, webp 형식의 이미지를 업로드하세요."
                    )
                else:
                    # 업로드된 이미지를 GitHub에 업로드
                    try:
                        img_url = upload_to_github(img_path, repo)
                        st.session_state["img_url"] = img_url
                        st.session_state["result_file"] = describe(img_url)
                    except Exception as e:
                        st.error(f"이미지 업로드에 실패했습니다: {e}")
            except Exception as e:
                st.error(f"이미지 형식을 확인하는 중 오류가 발생했습니다: {e}")
        else:
            st.warning("이미지 파일을 업로드하세요!")

    if "img_path" in st.session_state:
        st.image(
            st.session_state["img_path"],
            caption="업로드된 이미지",
            use_container_width=True,
        )
    if "result_file" in st.session_state:
        st.success(st.session_state["result_file"])
