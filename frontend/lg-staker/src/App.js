import React, { useState, useEffect } from "react";
import Login from "./components/Login";
import Dashboard from "./components/Dashboard";
import { AuthContext } from "./context";

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState("");

  const [user, setUser] = useState("");
  useEffect(() => {
    const token_verification = async () => {
      let token = sessionStorage.getItem("token"); // get token
      if (!token || token === undefined || token === "") {
        // check if the token is present or not if no then dont do anything
        setIsLoggedIn(false);
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
  const base_url = process.env.REACT_APP_API_URI;

  return (
    <AuthContext.Provider
      value={{ base_url, isLoggedIn, setIsLoggedIn, user, setUser }}
    >
      <div className="my-3">
        {isLoggedIn === true && isLoggedIn !== "" ? (
          <Dashboard />
        ) : isLoggedIn === false && isLoggedIn !== "" ? (
          <Login />
        ) : (
          ""
        )}
      </div>
    </AuthContext.Provider>
  );
}

export default App;
