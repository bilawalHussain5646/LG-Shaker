import React, { useState, useContext, useEffect } from "react";
import { AuthContext } from "../context";

const Login = () => {
  const { base_url, setIsLoggedIn, setUser } = useContext(AuthContext);
  const [state, setState] = useState({
    email: "",
    password: "",
  });

  useEffect(() => {
    const token_verification = async () => {
      let token = sessionStorage.getItem("token"); // get token
      if (!token || token === undefined || token === "") {
        // check if the token is present or not if no then dont do anything
      } else {
        // else send a request to the route and validate whether the token is valid or not
        let result = await fetch(`${base_url}/user-info`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }).catch((err) => {
          console.log(err);
        });

        if (result && result.ok) {
          let data = await result.json();
          setIsLoggedIn(true);
          setUser(data);
        } else {
          sessionStorage.clear();
          setIsLoggedIn(false);
          setUser("");
        }
      }
    };
    token_verification();

    // Send the token in the
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // for verifying the token and protect login

  const update = (event) => {
    const target = event.currentTarget;

    setState({
      ...state,
      [target.name]: target.type === "checkbox" ? target.checked : target.value,
    });
  };
  const handleLogin = async (event) => {
    event.preventDefault();
    let bodyFormData = new FormData();
    bodyFormData.append("email", state.email);
    bodyFormData.append("password", state.password);
    try {
      let res = await fetch(`${base_url}/signin`, {
        method: "POST",
        body: bodyFormData,
      }).catch((err) => {
        console.log(err);
      });
      // We will get  the access token cookie and refresh token cookie and it will be stored in react page

      const response = await res.json();

      if (!res.ok) {
        console.log(response.msg);
        // failed to logged in show in form
      } else {
        sessionStorage.setItem("token", response.token);
        setIsLoggedIn(true);

        // Redirect to dashboard
        //
        console.log(response.msg);
      }
    } catch (err) {
      // console.log(err.status);
    }
  };

  return (
    <div
      className="container mx-auto h-100 custom-width"
      style={{ paddingBottom: "150px", maxWidth: "650px" }}
    >
      <div>
        <div className="row d-flex align-items-center" style={{ color: "#494c4f" }}>
          <div className="col-12 text-center mt-5">
            <h3 className="p-3">
              <span className="" style={{ color: "#494c4f" }}>
                Admin&nbsp;
              </span>
              Login Area
            </h3>
          </div>
        </div>
        <div className="d-flex justify-content-center">
          <form className="row text-dark body-form-custom rounded">
            {/* {% with messages = get_flashed_messages(with_categories=true) %} {% if messages %} {% for category, message in messages %}
  <div className="col-12 alert alert-{{category}}" role="alert">
    {{ message }}
  </div>
  {% endfor %} {% endif %} {% endwith %} */}
            <div className="col-12 mb-3">
              <label htmlFor="email" className="form-label">
                Email ID <span className="text-danger">*</span>
              </label>
              <input
                type="email"
                onChange={update}
                className="form-control"
                name="email"
                id="email"
                aria-describedby="emailHelp"
                required
              />
            </div>
            <div className="col-12 mb-4">
              <label htmlFor="password" className="form-label">
                Password <span className="text-danger">*</span>
              </label>
              <input
                type="password"
                onChange={update}
                id="password"
                name="password"
                required
                className="form-control"
              />
            </div>

            <div className="row m-0">
              <button className="col-12 btn btn-danger w-100" onClick={handleLogin}>
                Login
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
