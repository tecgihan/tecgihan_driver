# tecgihan_driver パッケージメンテナンス


## ローカル debian パッケージの作成

後述のネットワーク経由で debian パッケージを `apt` インストールできる `rosdistro` への反映がされていない状況などで最新のコードからローカルファイルとして `debian` パッケージを作成するための作業です．

詳しくは "[ROS 2 Documentation: Jazzy - Building a custom deb package](https://docs.ros.org/en/jazzy/How-To-Guides/Building-a-Custom-Deb-Package.html)" に説明があります．

- [ROS 2 Documentation: Jazzy - Building a custom deb package](https://docs.ros.org/en/jazzy/How-To-Guides/Building-a-Custom-Deb-Package.html)
  - https://docs.ros.org/en/jazzy/How-To-Guides/Building-a-Custom-Deb-Package.html


### 準備作業

ローカルで debian パッケージを作成するために必要なソフトウェアをインストールしていない場合は次のようにコマンドを実行してください．

``` bash
sudo apt install python3-bloom python3-rosdep fakeroot debhelper dh-python
sudo rosdep init
rosdep update
```

### debian パッケージの作成

パッケージディレクトリ内に中間ファイルが多く作成されるので普段のワークスペースではなく `/tmp` フォルダ内に `tecgihan_driver` を `git clone` して作業することを推奨します．

一般的に `/tmp` ディレクトリは一時的なファイルを置いておくディレクトリでシステム再起動時に中にあるファイルは自動的に削除されます．

``` bash
cd /tmp
git clone https://github.com/tecgihan/tecgihan_driver.git
cd /tmp/tecgihan_driver
bloom-generate rosdebian
fakeroot debian/rules binary
```

`tecgihan_driver` ディレクトリの1つ上のディレクトリ（ 上記実行例では `/tmp` ）に debian パッケージファイルが作成されます．

``` bash
cd /tmp
ls *.deb
```

**出力例**
``` bash
robotuser@robotuser-PC:/tmp$ ls *.deb
ros-jazzy-tecgihan-driver_0.1.1-0noble_amd64.deb
robotuser@robotuser-PC:/tmp$ 
```

作成された debian ファイルを `/tmp` に置いたままにすると PC 再起動時などに消去されてしまうので他の `~/Documents` などのユーザのフォルダに移動しておくと良いでしょう．

**コピーコマンド実行例**
``` bash
cp ros-jazzy-tecgihan-driver_0.1.1-0noble_amd64.deb ~/Documents/
```

**移動コマンド実行例**
``` bash
mv ros-jazzy-tecgihan-driver_0.1.1-0noble_amd64.deb ~/Documents/
```

### ローカルファイルの debian パッケージからインストール

``` bash
sudo apt install ./ros-jazzy-tecgihan-driver_0.1.1-0noble_amd64.deb
```

`apt` インストールに伴い設定されるデバイス利用権限をもつユーザグループを反映するには、以下のいずれかを行ってください：

1. 一度ログアウトしてから再ログイン（推奨）
2. または、現在のターミナルで `newgrp dialout` を実行

<br>


## ROS パッケージのリリース

tecgihan_driver を ROS パッケージとしてネットワーク経由で debian パッケージインストールできるようにするための作業です．

- [ROS 2 Documentation: Jazzy - Subsequent Releases](https://docs.ros.org/en/jazzy/How-To-Guides/Releasing/Subsequent-Releases.html)
  - https://docs.ros.org/en/jazzy/How-To-Guides/Releasing/Subsequent-Releases.html


### 準備作業

事前に次の準備が整っていることを確認してください．

- GitHub 上の `tecgihan_driver` へのプルリクエスト（Pull Request / PR）が来たときにテストが正常に通っていることとコード自体も正常に機能することを確認してから `main` ブランチにマージ（Merge）されていること
  - テストで `rosdistro` へのプルリクエストがマージされるためのいくつかの条件が達成されていることが確認される
  - テスト内容は [tecgihan_driver / .github / workflows / ci.yaml](../.github/workflows/ci.yaml) にて記述
- 作業者が GitHub アカウントを持っている
- 予め作業者の GitHub アカウントに ROS の `rosdistro` リポジトリがフォーク（Fork）されている


### 依存パッケージのインストール

``` bash
sudo apt install python3-bloom python3-catkin-pkg
sudo rosdep init
rosdep update
```

### GitHub アクセストークンの設定

コマンドラインから GitHub にアクセスするためのトークンの設定をします．下記 Web ページを参考に進めてください．

- Set up a Personal Access Token
  - https://docs.ros.org/en/jazzy/How-To-Guides/Releasing/Subsequent-Releases.html#set-up-a-personal-access-token


### 作業フォルダの準備

`/tmp` フォルダ内に `tecgihan_driver` を `git clone` して作業することを推奨します．

``` bash
cd /tmp
git clone https://github.com/tecgihan/tecgihan_driver.git
cd /tmp/tecgihan_driver
```


### Changelog の更新

`catkin_generate_changelog` コマンドを実行し，`CHANGELOG.rst` ファイルを編集して変更ログを更新します．

- Updating Changelog
  - https://docs.ros.org/en/jazzy/How-To-Guides/Releasing/Subsequent-Releases.html#updating-changelog

``` bash
catkin_generate_changelog
```


### パッケージバージョンを上げる

`catkin_prepare_release` コマンドを実行してパッケージバージョンを上げます．

- Bump the package version
  - https://docs.ros.org/en/jazzy/How-To-Guides/Releasing/Subsequent-Releases.html#bump-the-package-version

``` bash
catkin_prepare_release
```


### パッケージのリリース

Bloom ツールを使って ROS パッケージをリリースします．

- Bloom Release
  - https://docs.ros.org/en/jazzy/How-To-Guides/Releasing/Subsequent-Releases.html#bloom-release

**ROS Humble の場合**
``` bash
bloom-release --new-track --rosdistro humble --track humble tecgihan_driver
```

**ROS Jazzy の場合**
``` bash
bloom-release --new-track --rosdistro jazzy --track jazzy tecgihan_driver
```

`bloom-release` 実行中に入力する情報は次のとおりです．

- Release repository url: https://github.com/tecgihan/tecgihan_driver-release.git
- Repository Name: tecgihan_driver
- Upstream Repository URI: https://github.com/tecgihan/tecgihan_driver.git
- Upstream VCS Type: git
- Version: {auto}
- Release Tag: {version}
- Upstream Devel Branch: main
- ROS Distro: jazzy
  - Humble の場合は humble
- Release Repository Push URL: {none}
- `Open a pull request from '$YOUR_GITHUB_ACCOUNT/rosdistro:bloom-tecgihan_driver-0' into 'ros/rosdistro:master'?
Continue [Y/n]? y`


### ROS パッケージリリース達成状況の確認

`rosdistro` へのプルリクエストがマージされた後に `tecgihan_driver` ROS パッケージのリリース達成状況を確認するには次の Web サイトにアクセスしてください．

- ROS Packages for Humble - tecgihan_driver
  - https://repo.ros2.org/status_page/ros_humble_default.html?q=tecgihan_driver
- ROS Packages for Jazzy - tecgihan_driver
  - https://repo.ros2.org/status_page/ros_jazzy_default.html?q=tecgihan_driver

各四角マークの説明は次のとおりです．

- 左 = building
- 中 = testing
- 右 = main → ここが緑色になっているとネットワークから `apt` でインストール可能
