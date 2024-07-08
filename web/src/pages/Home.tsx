import { useEffect, useState } from 'react';
import api from '../api';

function HomePage() {
  const [text, setText] = useState('');

  useEffect(() => {
    api.get('/secured_resource').then((response) => {
      setText(response.data.message);
    });
  }, []);

  return (
    <>
      <h1>VReact + Flask OAuth example</h1>
      <a href='/oauth/logout'>Log Out</a>
      {text && <p>SECURED DATA: {text}</p>}
    </>
  );
}

export default HomePage;
